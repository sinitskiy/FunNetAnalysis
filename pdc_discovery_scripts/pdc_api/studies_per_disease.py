'''
Get all pdc_study_id in the PDC database for a disease type.

documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Program/programsProjectsStudies
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .utils.make_query import make_query
from .utils.waiter import Waiter


class _Study(BaseModel):
    pdc_study_id: str


class _Project(BaseModel):
    studies: list[_Study]


class _Program(BaseModel):
    projects: list[_Project]


class _Data(BaseModel):
    programsProjectsStudies: list[_Program]


class _QueryResponse(BaseModel):
    data: _Data


async def studies_per_disease(
    *,
    client: AsyncClient,
    waiter: Waiter,
    disease_type: str,
):
    '''
    Get all pdc_study_id in the PDC database for a given disease type.
    '''

    query = f'''
        query {{
            programsProjectsStudies(disease_type: "{disease_type}") {{
                projects {{
                    studies {{
                        pdc_study_id
                    }}
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

    pdc_study_ids = []

    for program in response.data.programsProjectsStudies:
        for project in program.projects:
            for study in project.studies:
                pdc_study_ids.append(study.pdc_study_id)

    return pdc_study_ids
