import pandas as pd
df = pd.read_csv("sf311_raw.csv")
df.info()
df.head()
df.isna().mean().sort_values(ascending=False)           # share of nulls per column
df["service_name"].value_counts().head(15)
df["status_description"].value_counts()
df["analysis_neighborhood"].nunique()

print(df["requested_datetime"].min())
print(df["status_description"].value_counts())
