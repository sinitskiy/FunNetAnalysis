'''
Get all pdc_study_id from the PDC API.

documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Study/studyCatalog
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .utils.make_query import make_query
from .utils.waiter import Waiter


class _Study(BaseModel):
    pdc_study_id: str


class _Data(BaseModel):
    studyCatalog: list[_Study]


class _QueryResponse(BaseModel):
    data: _Data


async def all_studies(
    *,
    client: AsyncClient,
    waiter: Waiter,
):
    '''
    Get all pdc_study_id from the PDC API.
    '''

    query = '''
        query {
            studyCatalog {
                pdc_study_id
            }
        }
    '''

    response = await make_query(
        client=client,
        waiter=waiter,
        query=query,
        model=_QueryResponse,
    )

    pdc_study_ids = [
        study.pdc_study_id
        for study in response.data.studyCatalog
    ]

    return pdc_study_ids
