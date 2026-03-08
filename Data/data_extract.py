# Importing necessary libraries
import asyncio
import os
import sys
from typing import List, Tuple

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime

from Data.db_conn import connect_to_db, insert_data
from Logs.logs import api_logger

url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"


async def api_insertion(
    records: List[Tuple[datetime, str, float]], batch_size=1000
) -> List[Tuple[datetime, str, float]]:
    try:
        page_size = 100
        page_num = 1
        total_inserted = 0  # Initialize once outside loop
        total_skipped = 0  # Initialize once outside loop

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0)
        ) as client:
            while True:
                params = {"page[size]": page_size, "page[number]": page_num}
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    api_logger.error(
                        f"API error {response.status_code}: {response.text}"
                    )
                    break

                data = response.json()
                items = data.get("data", [])

                if not items:
                    api_logger.info("No more data. Ending pagination.")
                    break

                for item in items:
                    raw_value = item["avg_interest_rate_amt"]
                    clean_value = (
                        round(float(raw_value.replace("%", "")) / 100, 6)
                        if raw_value and raw_value.lower() != "null"
                        else 0
                    )
                    record_date = datetime.strptime(
                        item["record_date"], "%Y-%m-%d"
                    ).date()
                    records.append(
                        (
                            record_date,
                            item["security_type_desc"],
                            item["security_desc"],
                            clean_value,
                        )
                    )

                # Process batches
                while len(records) >= batch_size:
                    batch = records[:batch_size]
                    result = await insert_data(batch, batch_size=batch_size)

                    # Handle dict return
                    inserted_count = result["total_inserted"]
                    skipped_count = result["total_skipped"]

                    total_inserted += inserted_count
                    total_skipped += skipped_count

                    api_logger.info(
                        f"Batch: {inserted_count} inserted, {skipped_count} skipped (attempted {len(batch)})"
                    )
                    records = records[batch_size:]

                page_num += 1
                await asyncio.sleep(1)

        # Handle leftover records
        if records:
            result = await insert_data(records, batch_size=len(records))
            total_inserted += result["total_inserted"]
            total_skipped += result["total_skipped"]
            api_logger.info(
                f"Leftover: {result['total_inserted']} inserted, {result['total_skipped']} skipped (attempted {len(records)})"
            )

        api_logger.info(
            f"FINISHED. Total inserted: {total_inserted}, Total skipped: {total_skipped}"
        )

    except Exception as e:
        api_logger.exception(f"Unexpected failure: {e}")


async def main():
    await connect_to_db()
    await api_insertion(records=[])


asyncio.run(main())
