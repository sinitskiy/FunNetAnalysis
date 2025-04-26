import os
import asyncio

import httpx

import pandas as pd

from datacommons_api.waiter import Waiter

from datacommons_api.files import query_files_per_study

STUDIES = ('PDC000109', 'PDC000111')


async def main():
    waiter = Waiter(interval=0.5)
    transport = httpx.AsyncHTTPTransport(retries=3)

    # { file_id: signed_url }
    signed_urls: dict[str, str] = {}

    async with httpx.AsyncClient(timeout=10., transport=transport) as client:
        for pdc_study_id in STUDIES:
            files = await query_files_per_study(
                client=client,
                waiter=waiter,
                pdc_study_id=pdc_study_id,
            )

            for file in files:
                signed_urls[file.file_id] = file.signedUrl.url

    for csv_path in os.listdir('old'):
        if not csv_path.endswith('.csv'):
            continue

        df = pd.read_csv(f'old/{csv_path}')
        for file_id in df['file_id']:
            df.loc[df['file_id'] == file_id,
                   'File Download Link'] = signed_urls[file_id]

        df.to_csv(f'new/{csv_path}', index=False)

if __name__ == '__main__':
    asyncio.run(main())
