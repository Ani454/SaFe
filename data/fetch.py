import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

URL = "https://data.sfgov.org/resource/vw6y-z8j6.json"
HEADERS = {}
if os.getenv("SOCRATA_APP_TOKEN"):
    HEADERS["X-App-Token"] = os.getenv("SOCRATA_APP_TOKEN")

FIELDS = ",".join([
    "service_request_id", "requested_datetime", "closed_date",
    "status_description", "status_notes", "service_name",
    "service_subtype", "address", "analysis_neighborhood",
    "lat", "long",
])

def fetch(max_rows=100000, page_size=10000):
    rows, offset = [], 0
    while offset < max_rows:
        params = {
            "$select": FIELDS,
            "$where": "requested_datetime > '2026-08-01T00:00:00'",
            "$order": "requested_datetime DESC, service_request_id",
            "$limit": min(page_size, max_rows - offset),
            "$offset": offset,
        }
        r = requests.get(URL, params=params, headers=HEADERS, timeout=60)
        r.raise_for_status()
        batch = r.json()
        print(f"offset {offset}: {len(batch)} rows")
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
        if len(batch) < params["$limit"]:
            break
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = fetch()
    df.to_csv("sf311_raw.csv", index=False)
    print(df.shape)