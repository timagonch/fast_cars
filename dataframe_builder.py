import json
import pandas as pd
from pathlib import Path

# Load JSON from file
json_path = Path("fastest_cars_data.json")
cars = json.loads(json_path.read_text(encoding="utf-8"))

df = pd.DataFrame(cars)

# Standardize column names
rename_map = {
    "Year": "year",
    "Make and model": "make_model",
    "Horsepower": "horsepower",
    "Top speed (km/h)": "top_speed_kmh",
    "Engine displacement (L)": "engine_displacement_l",
    "Engine type": "engine_type",
}
df = df.rename(columns=rename_map)

# Coerce types, but don’t drop nulls
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["horsepower"] = pd.to_numeric(df["horsepower"], errors="coerce").astype("Int64")
df["top_speed_kmh"] = pd.to_numeric(df["top_speed_kmh"], errors="coerce").astype("Int64")
df["engine_displacement_l"] = pd.to_numeric(df["engine_displacement_l"], errors="coerce").astype(float)

# uv add supabase pandas python-dotenv
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Convert DataFrame -> list of dicts
records = df.to_dict(orient="records")

# Insert in batches to avoid payload size issues
BATCH_SIZE = 500
for i in range(0, len(records), BATCH_SIZE):
    chunk = records[i:i+BATCH_SIZE]
    response = supabase.table("fastest_cars").insert(chunk).execute()
    print(f"Inserted batch {i//BATCH_SIZE + 1}, count={len(chunk)}")

print(f"✅ Uploaded {len(records)} rows to Supabase table `fastest_cars`")

