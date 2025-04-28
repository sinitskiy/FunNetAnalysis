'''
main entry point
'''

import itertools
import asyncio
from typing import TypeVar
from typing import Awaitable

import httpx

import pandas as pd

from pdc_api.utils.waiter import Waiter

from pdc_api.all_studies import all_studies
from pdc_api.all_file_metadata import all_file_metadata
from pdc_api.clinicals_per_study import clinicals_per_study
from pdc_api.clinicals_per_study import _ClinicalDatum
from pdc_api.files_per_study import files_per_study
from pdc_api.files_per_study import _File

T = TypeVar('T')


async def _resolve_all_tasks(
    coroutines: list[Awaitable[T]],
):
    tasks: list[asyncio.Task[T]] = []

    async with asyncio.TaskGroup() as tg:
        for coroutine in coroutines:
            tasks.append(tg.create_task(coroutine))

    results = [
        task.result()
        for task in tasks
    ]

    return results


async def main():
    '''
    main entry point
    '''
    transport = httpx.AsyncHTTPTransport(retries=5)
    waiter = Waiter()

    async with httpx.AsyncClient(
        timeout=10,
        transport=transport,
    ) as client:
        # ------------------- 1 -------------------
        print('retrieving all pdc_study_ids')
        pdc_study_ids = await all_studies(
            client=client,
            waiter=waiter,
        )

        df = pd.DataFrame.from_records(
            [
                {'pdc_study_id': pdc_study_id}
                for pdc_study_id in pdc_study_ids
            ],
            index='pdc_study_id',
        )
        df.to_csv('wd/pdc_study_ids.csv')

        # ------------------- 2 -------------------
        print('retrieving all file metadata with specified formats')
        metadata = await all_file_metadata(
            client=client,
            waiter=waiter,
        )
        df = pd.DataFrame.from_records(
            [
                {
                    'file_id': file_metadata.file_id,
                    'file_name': file_metadata.file_name,
                    'file_location': file_metadata.file_location,
                    'num_aliquots': len(file_metadata.aliquots),
                }
                for file_metadata in metadata
            ],
            index='file_id',
        )
        df.to_csv('wd/file_metadata.csv')

        # ------------------- 3 -------------------
        print('retrieving all clinical data for each pdc_study_id')
        tasks = [
            clinicals_per_study(
                client=client,
                waiter=waiter,
                pdc_study_id=pdc_study_id,
            )
            for pdc_study_id in pdc_study_ids
        ]
        results: list[list[_ClinicalDatum]] = await _resolve_all_tasks(tasks)
        clinical_data = list(itertools.chain.from_iterable(results))
        df = pd.DataFrame.from_records(
            [
                {
                    'case_id': datum.case_id,
                    'pdc_study_id': datum.pdc_study_id,
                    'disease_type': datum.disease_type,
                    'tumor_stage': datum.tumor_stage,
                    'num_samples': len(datum.samples),
                }
                for datum in clinical_data
            ],
            index='case_id',
        )
        df.to_csv('wd/clinical_data.csv')

        sample_id_to_case_id = {}
        for datum in clinical_data:
            for sample in datum.samples:
                sample_id_to_case_id[sample.sample_id] = datum.case_id

        case_id_to_case_info = {
            datum.case_id: (
                datum.pdc_study_id,
                datum.disease_type,
                datum.tumor_stage,
            )
            for datum in clinical_data
        }

        # ------------------- 4 -------------------
        print('identifying files that can be uniquely mapped to a case_id')

        num_not_mapped = 0
        num_uniquely_mapped = 0
        num_nonuniquely_mapped = 0

        unambiguous = []

        for file_metadata in metadata:
            mapped_case_ids = {
                aliquot.case_id for aliquot in file_metadata.aliquots}
            mapped_sample_ids = {
                aliquot.sample_id for aliquot in file_metadata.aliquots}

            for sample_id in mapped_sample_ids:
                if sample_id in sample_id_to_case_id:
                    mapped_case_ids.add(sample_id_to_case_id[sample_id])
                # else:
                #     print(
                #         f'WARNING: sample_id {sample_id} not found in clinical data'
                #     )

            case_infos: set[tuple[str, str, str]] = set()
            for case_id in mapped_case_ids:
                if case_id in case_id_to_case_info:
                    case_infos.add(case_id_to_case_info[case_id])
                # else:
                #     print(
                #         f'WARNING: case_id {case_id} not found in clinical data',
                #     )

            if len(case_infos) == 0:
                num_not_mapped += 1
            elif len(case_infos) == 1:
                num_uniquely_mapped += 1
                case_info = case_infos.pop()
                unambiguous.append({
                    'file_id': file_metadata.file_id,
                    'file_name': file_metadata.file_name,
                    'file_location': file_metadata.file_location,
                    'pdc_study_id': case_info[0],
                    'disease_type': case_info[1],
                    'tumor_stage': case_info[2],
                })
            else:
                num_nonuniquely_mapped += 1

        df = pd.DataFrame.from_records(
            unambiguous,
            index='file_id',
        )
        df.to_csv('wd/unambiguous_file_metadata.csv')

        print(
            f'\tnum files not mapped to any case information: {num_not_mapped}',
        )
        print(
            f'\tnum files mapped to a unique case information: {num_uniquely_mapped}',
        )
        print(
            f'\tnum files mapped to ambiguous case information: {num_nonuniquely_mapped}',
        )

        view = df.loc[df['tumor_stage'] != 'Not Reported']
        useful_pdc_study_ids = view['pdc_study_id'].unique()
        print(
            f'\tdisease types with tumor stage information: {view["disease_type"].unique()}',
        )
        print(
            f'\tstudies with tumor stage information: {useful_pdc_study_ids}')

        # ------------------- 5 -------------------
        print('retrieving download URLs for each file')
        tasks = [
            files_per_study(
                client=client,
                waiter=waiter,
                pdc_study_id=pdc_study_id,
                # update=True, # uncomment to update download URLs
            )
            for pdc_study_id in useful_pdc_study_ids
        ]

        results: list[list[_File]] = await _resolve_all_tasks(tasks)
        download_urls: dict[str, str] = {}
        for files in results:
            for file in files:
                download_urls[file.file_id] = file.signedUrl.url

        df = view.copy()
        df['download_url'] = df.index.map(download_urls)
        df.to_csv('wd/unambiguous_file_metadata_with_urls.csv')

if __name__ == '__main__':
    asyncio.run(main())
