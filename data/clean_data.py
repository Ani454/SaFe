import pandas as pd

df = pd.read_csv("sf311_raw.csv", dtype={"service_request_id": str})

# Coordinates: numeric, non-null, and inside SF's rough bounding box
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["long"] = pd.to_numeric(df["long"], errors="coerce")
df = df.dropna(subset=["lat", "long"])
df = df[df["lat"].between(37.6, 37.85) & df["long"].between(-122.53, -122.35)]

# Dates (Socrata returns local SF time with no timezone)
df["requested_datetime"] = pd.to_datetime(df["requested_datetime"], errors="coerce")
df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")

# Resolution time; stays NaN for open cases
df["resolution_hours"] = (
    (df["closed_date"] - df["requested_datetime"]).dt.total_seconds() / 3600
)
# Remove bad data: closed before it was opened
df.loc[df["resolution_hours"] < 0, "resolution_hours"] = None

# Dedupe on the case id
df = df.drop_duplicates(subset="service_request_id")

df.to_csv("sf311_clean.csv", index=False)
df.to_parquet("sf311_clean.parquet", index=False)
print(df.shape)
print(df["resolution_hours"].describe())
print(pd.read_parquet("sf311_clean.parquet").dtypes)
