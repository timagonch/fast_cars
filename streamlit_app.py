# streamlit_app.py
import os
import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Page config should be first in Streamlit ---
st.set_page_config(page_title="Fastest Cars Timeline", layout="wide")

# --- Config ---
TABLE_NAME = "fastest_cars"    
TIMESTAMP_COL = "scraped_at"    

# --- Load env vars (Modal injects these as secrets in prod) ---
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]  # fix name (was SUPABASE_KEY before)

# --- Connect to Supabase once ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- Latest 10 entries table (by timestamptz, hide id) ---
@st.cache_data(ttl=30)
def fetch_latest_rows(_sb: Client) -> pd.DataFrame:
    resp = (
        _sb.table(TABLE_NAME)
        .select("*")
        .order(TIMESTAMP_COL, desc=True)
        .limit(10)
        .execute()
    )
    data = resp.data or []
    df = pd.DataFrame(data)

    # drop id column if present
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # pretty timestamptz
    if TIMESTAMP_COL in df.columns:
        df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], utc=True)
        cols = [TIMESTAMP_COL] + [c for c in df.columns if c != TIMESTAMP_COL]
        df = df[cols]

    return df


st.title("🚗 Fastest Cars Timeline")

st.subheader("Latest 10 entries")
try:
    latest_df = fetch_latest_rows(supabase)
    if latest_df.empty:
        st.info("No rows found.")
    else:
        st.dataframe(latest_df, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Failed to load data: {e}")

st.markdown("Scatterplot of **Top Speed (km/h)** vs **Year**")

# --- Main chart data ---
response = supabase.table(TABLE_NAME).select("*").execute()
if not response.data:
    st.warning("No data found in Supabase table.")
    st.stop()

df = pd.DataFrame(response.data)

# Ensure numeric columns are numeric
if "year" in df.columns:
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
if "top_speed_kmh" in df.columns:
    df["top_speed_kmh"] = pd.to_numeric(df["top_speed_kmh"], errors="coerce")

# Build scatter plot
fig = px.scatter(
    df,
    x="year",
    y="top_speed_kmh",
    hover_data=["make_model", "horsepower", "engine_displacement_l", "engine_type"],
    color="engine_type",
    labels={"year": "Year", "top_speed_kmh": "Top Speed (km/h)"},
    title="Top Speed vs Year (Hover for Details)",
)

st.plotly_chart(fig, use_container_width=True)
