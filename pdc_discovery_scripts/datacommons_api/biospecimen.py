'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/General/biospecimenPerStudy
'''

from collections import defaultdict

from httpx import AsyncClient
from pydantic import BaseModel

from .query_pdc import query_pdc


class _Biospeciman(BaseModel):
    sample_id: str
    sample_type: str


class _Data(BaseModel):
    biospecimenPerStudy: list[_Biospeciman]


class _QueryResponse(BaseModel):
    data: _Data


async def query_biospecimen_per_study(
    client: AsyncClient,
    *,
    pdc_study_id: str,
):
    '''
    Query the PDC API for biospecimen data in a given study.
    '''

    query = f'''query {{
    biospecimenPerStudy(pdc_study_id: "{pdc_study_id}") {{
        sample_id
        sample_type
    }}
}}'''

    response = await query_pdc(client, query, _QueryResponse)

    biospeciman_by_type: dict[str, set[str]] = defaultdict(set)

    for biospeciman in response.data.biospecimenPerStudy:
        biospeciman_by_type[biospeciman.sample_type].add(
            biospeciman.sample_id,
        )

    return biospeciman_by_type
