#!/usr/bin/env python3
import os
import asyncio

import httpx

from datacommons_api.studies import query_programs_projects_studies
from datacommons_api.biospecimen import query_biospecimen_per_study
from datacommons_api.files import query_files_per_study
from datacommons_api.file_metadata import query_file_metadata

# Folder to save downloaded files.
DOWNLOAD_DIR = "downloads"
PRIMARY_TUMOR_PATH = os.path.join(DOWNLOAD_DIR, "primary_tumor")
METASTATIC_PATH = os.path.join(DOWNLOAD_DIR, "metastatic")

os.makedirs(PRIMARY_TUMOR_PATH, exist_ok=True)
os.makedirs(METASTATIC_PATH, exist_ok=True)

DOWNLOAD_LOCK = asyncio.BoundedSemaphore(5)


async def _download_file(
    client: httpx.AsyncClient,
    url: str,
    file_path: str,
):
    if os.path.exists(file_path):
        return

    async with DOWNLOAD_LOCK:
        print(f"Downloading {url} to {file_path}")
        async with client.stream("GET", url) as response:
            with open(file_path, "wb") as file:
                async for chunk in response.aiter_bytes():
                    file.write(chunk)


async def main():
    '''
    aaa
    '''

    async with httpx.AsyncClient(timeout=10.) as client:
        pdc_study_ids = await query_programs_projects_studies(
            client,
            disease_type='Ovarian Serous Cystadenocarcinoma',
        )

        biospecimen_query_results: list[asyncio.Task] = []

        async with asyncio.TaskGroup() as tg:
            for pdc_study_id in pdc_study_ids:
                biospecimen_query_results.append(tg.create_task(
                    query_biospecimen_per_study(
                        client,
                        pdc_study_id=pdc_study_id,
                    ),
                ))

        biospecimen_type_info: dict[str, str] = {}

        for biospecimen_query_result in biospecimen_query_results:
            for sample_type, sample_ids in biospecimen_query_result.result().items():
                for sample_id in sample_ids:
                    biospecimen_type_info[sample_id] = sample_type

        files_query_results: list[asyncio.Task] = []

        async with asyncio.TaskGroup() as tg:
            for pdc_study_id in pdc_study_ids:
                files_query_results.append(tg.create_task(
                    query_files_per_study(
                        client,
                        pdc_study_id=pdc_study_id,
                    ),
                ))

        files: dict[str, tuple[str, str]] = {}
        for files_query_result in files_query_results:
            files.update(files_query_result.result())

        file_metadata = await query_file_metadata(
            client,
        )

        for file_id, (file_name, download_url) in list(files.items()):
            sample_ids = file_metadata[file_id]

            sample_types = {
                biospecimen_type_info[sample_id]
                for sample_id in sample_ids
            }

            # ???
            # assert len(sample_types) == 1, str(sample_types)
            # (sample_type, ) = sample_types

            for sample_type in sample_types:
                match sample_type:
                    case 'Primary Tumor':
                        await _download_file(
                            client,
                            download_url,
                            os.path.join(PRIMARY_TUMOR_PATH, file_name),
                        )
                    case 'Metastatic':
                        await _download_file(
                            client,
                            download_url,
                            os.path.join(METASTATIC_PATH, file_name),
                        )
                    case _:
                        continue


if __name__ == "__main__":
    asyncio.run(main())
