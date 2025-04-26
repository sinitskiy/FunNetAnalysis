'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Clinical/clinicalPerStudy
'''

from collections import defaultdict
from collections import Counter

from httpx import AsyncClient
from pydantic import BaseModel

from .waiter import Waiter
from .query_pdc import query_pdc


class _TumorSample(BaseModel):
    sample_id: str


class _ClinicalDatum(BaseModel):
    case_id: str
    disease_type: str = 'N/A'
    tumor_stage: str
    samples: list[_TumorSample]


class _Data(BaseModel):
    clinicalPerStudy: list[_ClinicalDatum]


class _QueryResponse(BaseModel):
    data: _Data


async def query_clinical_per_study(
    *,
    client: AsyncClient,
    waiter: Waiter,
    pdc_study_id: str,
) -> list[_ClinicalDatum]:
    '''
    Query the PDC API for clinical data in a given study.
    '''

    query = f'''query {{
    clinicalPerStudy(
        pdc_study_id: "{pdc_study_id}"
    ) {{
        case_id
        disease_type
        tumor_stage
        samples {{
            sample_id
        }}
    }}
}}'''

    try:
        response = await query_pdc(
            client=client,
            waiter=waiter,
            query=query,
            model=_QueryResponse,
        )
    except RuntimeError as e:
        print(
            f'error occurred while querying for clinical data in study {pdc_study_id}',
        )
        print(e)
        return []

    return response.data.clinicalPerStudy
