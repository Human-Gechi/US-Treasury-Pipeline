import requests
import pandas as pd
url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"

params = {}
response = requests.get(url, params=params)


if response.status_code == 200:
    data = response.json()

    for item in data.get("data", []):
        print(f"Date: {item['record_date']}, Type: {item['security_type_desc']}, Rate: {item['avg_interest_rate_amt']}")
else:
    print("Error fetching data:", response.status_code)
