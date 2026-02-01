import asyncio
import httpx
import hashlib
from db_conn import insert_data, connect_to_db, db_pool
from Logs.logs import api_logger
from datetime import datetime
url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"

async def api_insertion(batch_size=1000):
    try:
        seen = set()                
        records = []
        page_size = 100
        page_num = 1
        total_inserted = 0

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))  as client:
            while True:
                params = {"page[size]": page_size, "page[number]": page_num}
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    api_logger.error(f"API error {response.status_code}: {response.text}")
                    break

                data = response.json()
                items = data.get("data", [])

                if not items:
                    api_logger.info("No more data. Ending pagination.")
                    break

                for item in items:
                    raw_value = item['avg_interest_rate_amt']
                    clean_value = float(raw_value.replace("%","")) / 100 if raw_value and raw_value.lower() != "null" else 0
                    record_date = datetime.strptime(item["record_date"], "%Y-%m-%d").date()
                    key = (record_date, item['security_type_desc'], item['security_desc'])
                    if key in seen:
                        continue
                    seen.add(key)

                    records.append((record_date, item['security_type_desc'], item['security_desc'], clean_value))

                while len(records) >= batch_size:
                    batch = records[:batch_size]
                    inserted = await insert_data(batch, batch_size=batch_size)
                    api_logger.info(f"Inserted {inserted} rows (attempted {len(batch)}).")
                    total_inserted += inserted
                    records = records[batch_size:]

                page_num += 1
                await asyncio.sleep(1)


        if records:
            inserted = await insert_data(records, batch_size=len(records)) or 0
            total_inserted += inserted
            api_logger.info(f"Inserted remaining {inserted} leftover rows (attempted {len(records)}).")

        api_logger.info(f"FINISHED. Total rows inserted = {total_inserted}")

    except Exception as e:
        api_logger.exception(f"Unexpected failure: {e}")

async def main():
    await connect_to_db()
    await api_insertion()

if __name__ == "__main__":
    asyncio.run(main())