'''
unified query function for querying the PDC GrapyhQL API
'''

import hashlib

from typing import Type
from typing import TypeVar

from httpx import AsyncClient
from httpx import HTTPStatusError

from pydantic import BaseModel
from pydantic import ValidationError

from .waiter import Waiter
from .cache import Cache


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode('utf-8')).hexdigest()[:16]


T = TypeVar('T', bound=BaseModel)


async def make_query(
    *,
    client: AsyncClient,
    waiter: Waiter,
    query: str,
    model: Type[T],
    update: bool = False,
) -> T:
    '''
    Query the PDC API with a given query.
    '''

    payload = {
        'query': query,
    }

    headers = {
        'Content-Type': 'application/json',
    }

    query_cache = Cache(_cache_key(query), model)

    if (not update) and query_cache.exists:
        return query_cache.load()

    # cache does not exist, fetch data and update cache
    async with waiter.when_ready():
        response = await client.post(
            'https://proteomic.datacommons.cancer.gov/graphql',
            json=payload,
            headers=headers,
        )

        try:
            response.raise_for_status()
        except HTTPStatusError as e:
            with open('error.txt', 'wt', encoding='utf-8') as f:
                f.write(f'{e.__class__.__name__}\n\n')
                f.write(f'{e.args[0]}\n\n')

                f.write('Request:\n')
                f.write(f'\t{e.request.method} {e.request.url}\n')
                f.write(f'\theaders: {e.request.headers}\n')
                f.write(f'\tcontent: {e.request.content.decode("utf-8")}\n')

                f.write('\n')

                f.write('Response:\n')
                f.write(f'\tstatus: {e.response.status_code}\n')
                f.write(
                    f'\tcontent:\n\n{e.response.content.decode("utf-8")}\n'
                )

            raise RuntimeError(
                'HTTP error occurred while querying the PDC API. Content dumped to error.txt',
            ) from e

    try:
        data = model.model_validate_json(response.content)
    except ValidationError as e:
        with open('error.txt', 'wt', encoding='utf-8') as f:
            f.write(f'{e.error_count()} validation errors:\n')

            for i, error in enumerate(e.errors(), start=1):
                f.write('\n')
                f.write(f'{i}: {error["type"]}\n')
                f.write(f'\tlocation: {error["loc"]}\n')
                f.write(f'\tinput: {error["input"]}\n')
                f.write(f'\tmessage: {error["msg"]}\n')
                f.write('\n')

        raise RuntimeError(
            'Validation error occurred while parsing the PDC API response. Content dumped to error.txt',
        ) from e

    query_cache.update(data)

    return data
