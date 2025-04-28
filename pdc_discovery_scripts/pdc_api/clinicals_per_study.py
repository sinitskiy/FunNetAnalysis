'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Clinical/clinicalPerStudy
'''

from httpx import AsyncClient
from pydantic import BaseModel
from .utils.make_query import make_query
from .utils.waiter import Waiter


class _TumorSample(BaseModel):
    sample_id: str


class _ClinicalDatum(BaseModel):
    case_id: str
    pdc_study_id: str = ''
    disease_type: str
    tumor_stage: str
    samples: list[_TumorSample]


class _Data(BaseModel):
    clinicalPerStudy: list[_ClinicalDatum]


class _QueryResponse(BaseModel):
    data: _Data


async def clinicals_per_study(
    *,
    client: AsyncClient,
    waiter: Waiter,
    pdc_study_id: str,
):
    '''
    Get all clinical data for a given pdc_study_id.
    '''

    query = f'''
        query {{
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
        }}
    '''

    response = await make_query(
        client=client,
        waiter=waiter,
        query=query,
        model=_QueryResponse,
    )

    clinical_data = response.data.clinicalPerStudy
    for datum in clinical_data:
        datum.pdc_study_id = pdc_study_id

    return clinical_data
