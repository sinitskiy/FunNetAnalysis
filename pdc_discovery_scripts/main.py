
from collections import defaultdict
from collections import Counter

from itertools import chain

import asyncio

import httpx

import pandas as pd

from datacommons_api.waiter import Waiter

from datacommons_api.study_catalog import query_study_catalog

from datacommons_api.clinical import query_clinical_per_study
from datacommons_api.clinical import _ClinicalDatum

from datacommons_api.file_metadata import query_file_metadata

from datacommons_api.files import query_files_per_study
from datacommons_api.files import _File

# from datacommons_api.query_cache import QueryCache
# QueryCache.clear_all()


async def main():

    data = []
    # 1. query "studyCatalog" for all available studies

    waiter = Waiter(interval=0.5)
    transport = httpx.AsyncHTTPTransport(retries=3)

    counts: dict[str, Counter[str]] = defaultdict(Counter)

    async with httpx.AsyncClient(timeout=10., transport=transport) as client:
        # 1. query "studyCatalog" for all available studies
        res = await query_study_catalog(
            client=client,
            waiter=waiter,
        )

        pdc_study_ids = [study.pdc_study_id for study in res]
        print(pdc_study_ids)

        # 2. query "clinicalPerStudy" for all clinicals in each study
        clinial_query_results: list[asyncio.Task[list[_ClinicalDatum]]] = []

        async with asyncio.TaskGroup() as tg:
            for pdc_study_id in pdc_study_ids:
                clinial_query_results.append(tg.create_task(
                    query_clinical_per_study(
                        client=client,
                        waiter=waiter,
                        pdc_study_id=pdc_study_id,
                    ),
                ))

        clinicals = list(chain(
            *(res.result() for res in clinial_query_results)
        ))

        info_by_case_id = {
            clinical.case_id: (clinical.disease_type, clinical.tumor_stage)
            for clinical in clinicals
        }
        info_by_sample_id: dict[str, tuple[str, str]] = {}
        for clinical in clinicals:
            for sample in clinical.samples:
                info_by_sample_id[sample.sample_id] = (
                    clinical.disease_type,
                    clinical.tumor_stage,
                )

        # 2.5 query "filesPerStudy" for all files in each study
        files: dict[str, _File] = {}
        files_query_results: list[asyncio.Task[list[_File]]] = []
        async with asyncio.TaskGroup() as tg:
            for pdc_study_id in pdc_study_ids:
                files_query_results.append(tg.create_task(
                    query_files_per_study(
                        client=client,
                        waiter=waiter,
                        pdc_study_id=pdc_study_id,
                    ),
                ))

        for result in files_query_results:
            for file in result.result():
                files[file.file_id] = file

        # 3. query file_metadata
        file_metadata = await query_file_metadata(
            client=client,
            waiter=waiter,
        )

        print(len(file_metadata))
        print({
            '.'.join(md.file_name.split('.')[-2:])
            for md in file_metadata
        })

        for file_metadatum in file_metadata:
            if file_metadatum.file_name.endswith('.cap.psm'):
                continue

            assert file_metadatum.file_name.endswith('.mzid.gz')

            sample_ids = set(
                aliquot.sample_id for aliquot in file_metadatum.aliquots
            )
            case_ids = set(
                aliquot.case_id for aliquot in file_metadatum.aliquots)

            infos: set[tuple[str, str]] = set()

            for sample_id in sample_ids:
                if sample_id in info_by_sample_id:
                    infos.add(info_by_sample_id[sample_id])

            for case_id in case_ids:
                if case_id in info_by_case_id:
                    infos.add(info_by_case_id[case_id])

            disease_types = set(info[0] for info in infos)
            tumor_stages = set(info[1] for info in infos)

            counts[frozenset(disease_types)][frozenset(tumor_stages)] += 1

            if (len(disease_types) == 1) and (len(tumor_stages) == 1):
                (disease_type, ) = disease_types
                (tumor_stage, ) = tumor_stages

                if (disease_type == 'Other') or (tumor_stage == 'Not Reported'):
                    continue

                data.append({
                    'disease_type': disease_type,
                    'tumor_stage': tumor_stage,
                    'file_id': file_metadatum.file_id,
                    'file_name': file_metadatum.file_name,
                    'File Download Link': files[file_metadatum.file_id].signedUrl.url,
                })

            # if len(disease_types) > 1:
            #     disease_types.discard('Other')
            # if len(tumor_stages) > 1:
            #     tumor_stages.discard('Not Reported')

            # if len(disease_types) == 1 and len(tumor_stages) == 1:
            #     (disease_type, ) = disease_types
            #     (tumor_stage, ) = tumor_stages
            #     counts[disease_type][tumor_stage] += 1
            # else:
            #     print(file_metadatum.file_id, disease_types, tumor_stages)

    for disease_type, stage_counts in counts.items():
        stage_counts = {k: v for k, v in stage_counts.items() if len(k) == 1}
        if len(stage_counts) == 1 and frozenset({'Not Reported'}) in stage_counts.keys():
            continue
        print(", ".join(disease_type))
        for stage, count in stage_counts.items():
            print(f'\t{", ".join(stage)}: {count}')

    df = pd.DataFrame(data)
    df.to_csv('data.csv', index=False)

if __name__ == '__main__':
    asyncio.run(main())
