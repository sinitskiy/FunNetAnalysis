'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Files/filesPerStudy
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .waiter import Waiter
from .query_pdc import query_pdc


class _SignedUrl(BaseModel):
    url: str


class _File(BaseModel):
    file_id: str
    file_name: str
    signedUrl: _SignedUrl


class _Data(BaseModel):
    filesPerStudy: list[_File]


class _QueryResponse(BaseModel):
    data: _Data


async def query_files_per_study(
    *,
    client: AsyncClient,
    waiter: Waiter,
    pdc_study_id: str,
):
    '''
    Query the PDC API for files in a given study.
    '''

    query = f'''query {{
    filesPerStudy(
        pdc_study_id: "{pdc_study_id}"
        file_type: "Open Standard"
        data_category: "Peptide Spectral Matches"
    ) {{
        file_id
        file_name
        signedUrl {{
            url
        }}
    }}
}}'''

    response = await query_pdc(
        client=client,
        waiter=waiter,
        query=query,
        model=_QueryResponse,
    )

    return response.data.filesPerStudy
