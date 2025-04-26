'''
documentation:
https://proteomic.datacommons.cancer.gov/pdc/publicapi-documentation/#!/Program/programsProjectsStudies
'''

from httpx import AsyncClient
from pydantic import BaseModel

from .query_pdc import query_pdc


class _Study(BaseModel):
    pdc_study_id: str


class _Project(BaseModel):
    studies: list[_Study]


class _ProgramProjectStudy(BaseModel):
    projects: list[_Project]


class _Data(BaseModel):
    programsProjectsStudies: list[_ProgramProjectStudy]


class _QueryResponse(BaseModel):
    data: _Data


async def query_programs_projects_studies(
    client: AsyncClient,
    *,
    disease_type: str,
):
    '''
    Query the PDC API for studies in a given disease type.
    '''

    query = f'''query {{
    programsProjectsStudies(disease_type: "{disease_type}") {{
        projects {{
            studies {{
                pdc_study_id
            }}
        }}
    }}
}}'''

    response = await query_pdc(client, query, _QueryResponse)

    pdc_study_ids = []

    for pps in response.data.programsProjectsStudies:
        for project in pps.projects:
            for study in project.studies:
                pdc_study_ids.append(study.pdc_study_id)

    return pdc_study_ids
