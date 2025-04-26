'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Study/studyCatalog
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .query_pdc import query_pdc
from .waiter import Waiter


class _Study(BaseModel):
    pdc_study_id: str


class _Data(BaseModel):
    studyCatalog: list[_Study]


class _QueryResponse(BaseModel):
    data: _Data


async def query_study_catalog(
    *,
    client: AsyncClient,
    waiter: Waiter,
):
    '''
    Query the PDC API for all available studies.
    '''

    query = '''query {
    studyCatalog {
        pdc_study_id
    }
}'''

    response = await query_pdc(
        client=client,
        waiter=waiter,
        query=query,
        model=_QueryResponse,
    )

    return response.data.studyCatalog
