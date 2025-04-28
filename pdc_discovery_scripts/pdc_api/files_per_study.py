'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Files/filesPerStudy
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .utils.make_query import make_query
from .utils.waiter import Waiter


class _SignedUrl(BaseModel):
    url: str


class _File(BaseModel):
    file_id: str
    signedUrl: _SignedUrl


class _Data(BaseModel):
    filesPerStudy: list[_File]


class _QueryResponse(BaseModel):
    data: _Data


async def files_per_study(
    *,
    client: AsyncClient,
    waiter: Waiter,
    pdc_study_id: str,
    update: bool = False,
):
    '''
    Get all file data for a given pdc_study_id.
    '''

    query = f'''
        query {{
            filesPerStudy(
                pdc_study_id: "{pdc_study_id}"
                data_category: "Peptide Spectral Matches"
                file_type: "Open Standard"
                file_format: "mzIdentML"
                limit: 25000
            ) {{
                file_id
                signedUrl {{
                    url
                }}
            }}
        }}
    '''

    response = await make_query(
        client=client,
        waiter=waiter,
        query=query,
        model=_QueryResponse,
        update=update,
    )

    return response.data.filesPerStudy
