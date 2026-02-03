#Importing necessary libraries
import asyncio
import httpx
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_conn import insert_data,connect_to_db #Function to insert data
from Logs.logs import api_logger
from datetime import datetime
url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates" #API url

#Batch size for data insertion
async def api_insertion(batch_size=1000):
    try:
        records = [] #Total records
        page_size = 100 #Page size i.e no of records per page
        page_num = 1 #Initial page num
        total_inserted = 0 # Total number of records inserted

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))  as client: #Make a request
            while True:
                params = {"page[size]": page_size, "page[number]": page_num} #Url parameters
                response = await client.get(url, params=params) #Make a GET request

                if response.status_code != 200: #Status code is not OK
                    api_logger.error(f"API error {response.status_code}: {response.text}")
                    break #Break

                data = response.json() #Json data
                items = data.get("data", []) #Acessing data items

                if not items: #If no items
                    api_logger.info("No more data. Ending pagination.") #Log info
                    break

                for item in items: #Loop through items
                    raw_value = item['avg_interest_rate_amt'] #Get the raw value for avg_interest_rate_amt
                    clean_value = float(raw_value.replace("%","")) / 100 if raw_value and raw_value.lower() != "null" else 0 #Some data cleaning removing % sign and converting to decimal
                    record_date = datetime.strptime(item["record_date"], "%Y-%m-%d").date() #record date conversion
                    key = (record_date, item['security_type_desc'], item['security_desc']) #Unique key for each record

                    records.append((record_date, item['security_type_desc'], item['security_desc'], clean_value)) #Append records

                while len(records) >= batch_size: #While records are greater than batch size
                    batch = records[:batch_size] #Get the batch
                    inserted = await insert_data(batch, batch_size=batch_size) or 0 #Insert data
                    api_logger.info(f"Inserted {inserted} rows (attempted {len(batch)}).") #Log info
                    total_inserted += inserted #Increment total inserted count
                    records = records[batch_size:] #Update records

                page_num += 1 #Increment page num
                await asyncio.sleep(1) #Sleep for a second to avoid rate limiting

        if records: #If there are leftover records
            inserted = await insert_data(records, batch_size=len(records)) or 0 #Insert leftover records
            total_inserted += inserted #Update total inserted count
            api_logger.info(f"Inserted remaining {inserted} leftover rows (attempted {len(records)}).") #Log info

        api_logger.info(f"FINISHED.Total rows inserted = {total_inserted}") #Log total inserted count

    except Exception as e: #Unexpected errors
        api_logger.exception(f"Unexpected failure: {e}") #Log exception
