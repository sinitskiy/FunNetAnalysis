'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Files/fileMetadata
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .query_pdc import query_pdc
from .waiter import Waiter


class _Aliquot(BaseModel):
    sample_id: str
    case_id: str


class _FileMetadatum(BaseModel):
    file_id: str
    file_name: str
    file_location: str
    aliquots: list[_Aliquot]


class _Data(BaseModel):
    fileMetadata: list[_FileMetadatum]


class _QueryResponse(BaseModel):
    data: _Data


async def query_file_metadata(
    *,
    client: AsyncClient,
    waiter: Waiter,
):
    '''
    Query the PDC API for file metadata.
    '''

    query1 = '''query {
    fileMetadata(
        data_category: "Peptide Spectral Matches"
        file_type: "Open Standard"
        offset: 0
        limit: 25000
    ) {
        file_id
        file_name
        file_location
        aliquots {
            sample_id
            case_id
        }
    }
}'''
    query2 = '''query {
    fileMetadata(
        data_category: "Peptide Spectral Matches"
        file_type: "Open Standard"
        offset: 25000
        limit: 25000
    ) {
        file_id
        file_name
        file_location
        aliquots {
            sample_id
            case_id
        }
    }
}'''

    response1 = await query_pdc(
        client=client,
        waiter=waiter,
        query=query1,
        model=_QueryResponse,
    )

    response2 = await query_pdc(
        client=client,
        waiter=waiter,
        query=query2,
        model=_QueryResponse,
    )

    return [
        *response1.data.fileMetadata,
        *response2.data.fileMetadata,
    ]
