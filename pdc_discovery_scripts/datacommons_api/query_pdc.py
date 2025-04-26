'''
unified query function for GraphQL
'''

import hashlib

from typing import Type
from typing import TypeVar

from httpx import AsyncClient
# from httpx import HTTPStatusError

from pydantic import BaseModel
from pydantic import ValidationError

from .waiter import Waiter
from .query_cache import QueryCache

# LAST_OPERATION_TIME: float = 0.
# OPERATION_INTERVAL: float = 0.5


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode('utf-8')).hexdigest()[:16]


T = TypeVar('T', bound=BaseModel)


async def query_pdc(
    *,
    client: AsyncClient,
    waiter: Waiter,
    query: str,
    model: Type[T],
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

    with QueryCache(_cache_key(query), model) as qc:
        if not qc.exists:
            async with waiter.when_ready():
                response = await client.post(
                    'https://proteomic.datacommons.cancer.gov/graphql',
                    json=payload,
                    headers=headers,
                )

                response.raise_for_status()

            try:
                result = model.model_validate_json(response.text)
            except ValidationError as e:
                with open('error.txt', 'w', encoding='utf-8') as f:
                    f.write(response.text)

                raise RuntimeError(
                    'unparsable http response, error response dumped under ./error.txt',
                ) from e

            qc.update(result)

    assert qc.data is not None

    return qc.data
