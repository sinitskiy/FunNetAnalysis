'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Files/fileMetadata
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .utils.make_query import make_query
from .utils.waiter import Waiter


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


def _query(offset: int) -> str:
    return f'''
        query {{
            fileMetadata(
                data_category: "Peptide Spectral Matches"
                file_type: "Open Standard"
                file_format: "mzIdentML"
                offset: {offset}
                limit: 25000
            ) {{
                file_id
                file_name
                file_location
                aliquots {{
                    sample_id
                    case_id
                }}
            }}
        }}
    '''


async def all_file_metadata(
    *,
    client: AsyncClient,
    waiter: Waiter,
):
    '''
    Get all file metadata from the PDC API.
    '''

    metadata: list[_FileMetadatum] = []
    num_retrieved_prev_iter = -1

    while num_retrieved_prev_iter != 0:
        query = _query(len(metadata))
        response = await make_query(
            client=client,
            waiter=waiter,
            query=query,
            model=_QueryResponse,
        )

        metadata.extend(response.data.fileMetadata)
        num_retrieved_prev_iter = len(response.data.fileMetadata)

    return metadata
