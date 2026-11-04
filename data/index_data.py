"""
Phase 2: load the cleaned 311 CSV into Elasticsearch.

Run:  python index_sf311.py
Needs ES_URL and ES_API_KEY in .env, and the Phase 1 CSV at CSV_PATH.
Safe to re-run: it drops and recreates the index each time.
"""
import math
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

CSV_PATH = "sf311_clean.csv"   # change if your Phase 1 file has a different name
INDEX = "sf311"

FIELDS = [
    "service_request_id", "requested_datetime", "closed_date", "status_description",
    "service_name", "service_subtype", "analysis_neighborhood", "address",
    "status_notes", "resolution_hours", "location",
]

MAPPING = {
    "properties": {
        "service_request_id":    {"type": "keyword"},
        "requested_datetime":    {"type": "date"},
        "closed_date":           {"type": "date"},
        "status_description":    {"type": "keyword"},
        "service_name":          {"type": "keyword"},
        "service_subtype":       {"type": "keyword"},
        "analysis_neighborhood": {"type": "keyword"},
        "address":               {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "status_notes":          {"type": "text"},
        "resolution_hours":      {"type": "float"},
        "location":              {"type": "geo_point"},
    }
}


# ---------- Step 1: connect ----------
def connect():
    load_dotenv()
    es = Elasticsearch(os.environ["ES_URL"], api_key=os.environ["ES_API_KEY"])
    print("Connected to Elasticsearch", es.info()["version"]["number"])
    return es


# ---------- Step 2: create index with explicit mapping ----------
def create_index(es):
    es.options(ignore_status=404).indices.delete(index=INDEX)
    es.indices.create(index=INDEX, mappings=MAPPING)
    loc_type = es.indices.get_mapping(index=INDEX)[INDEX]["mappings"]["properties"]["location"]["type"]
    print(f"Created index '{INDEX}' (location type: {loc_type})")


# ---------- Step 3: load and prepare the CSV ----------
def load_dataframe():
    df = pd.read_csv(CSV_PATH)

    needed = [f for f in FIELDS if f != "location"] + ["lat", "long"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        sys.exit(f"CSV is missing columns: {missing}. Fix names in FIELDS or in Phase 1.")

    # Rebuild location from lat/long (a dict doesn't survive the CSV round trip)
    df = df.dropna(subset=["lat", "long"]).copy()
    df["location"] = [{"lat": float(a), "lon": float(b)} for a, b in zip(df["lat"], df["long"])]

    for col in ["requested_datetime", "closed_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df.loc[df["resolution_hours"] < 0, "resolution_hours"] = None

    print(f"Rows ready: {len(df)} | missing requested_datetime: {df['requested_datetime'].isna().sum()}")
    print("resolution_hours summary:\n", df["resolution_hours"].describe().round(1).to_string())
    return df


# ---------- Step 4: build bulk actions, dropping empty values ----------
def clean(v):
    if v is None or v is pd.NaT:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return v


def actions(df):
    for row in df[FIELDS].to_dict(orient="records"):
        doc = {k: clean(v) for k, v in row.items()}
        doc = {k: v for k, v in doc.items() if v is not None}
        yield {"_index": INDEX, "_id": str(row["service_request_id"]), "_source": doc}


# ---------- Step 5: bulk load and verify count ----------
def bulk_load(es, df):
    ok, errors = helpers.bulk(
    es.options(request_timeout=120), actions(df), chunk_size=1000, raise_on_error=False
)
    print(f"Indexed: {ok} | errors: {len(errors)}")
    for e in errors[:3]:
        print("  sample error:", e)

    es.indices.refresh(index=INDEX)
    count = es.count(index=INDEX)["count"]
    print(f"Index count: {count} | rows in CSV after cleaning: {len(df)}")
    if count != len(df):
        print("  Counts differ. Check errors above or duplicate service_request_id values.")


def main():
    es = connect()
    create_index(es)
    df = load_dataframe()
    bulk_load(es, df)
    print("Done.")


if __name__ == "__main__":
    main()