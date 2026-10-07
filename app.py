from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="311 Request Dashboard", page_icon="🏛️", layout="wide")

# Title and Short Description
st.title("🏛️ 311 Service Requests Dashboard (2025)")
st.markdown(
    """
    This interactive dashboard explores city-wide 311 service requests submitted during **2025**.
    Use the filters in the sidebar to choose a **date range**, **service types**, and **request status**.
    All metrics, charts, and the map update automatically.
    """
)

# 1. Load Data with Caching
DATA_FILE = Path(__file__).parent / "311_2025_dashboard.csv"
YEAR_START = date(2025, 1, 1)
YEAR_END = date(2025, 12, 31)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
    df = df[df["request_date"].dt.year == 2025]
    df["zipcode"] = df["zipcode"].astype("Int64").astype("string")
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data file {DATA_FILE.name}: {e}")
    st.stop()

min_possible_date = max(df["request_date"].min().date(), YEAR_START)
max_possible_date = min(df["request_date"].max().date(), YEAR_END)

# 2. Sidebar Filters
st.sidebar.header("Dashboard Filters")

start_date = st.sidebar.date_input(
    "Start Date", min_possible_date, min_value=min_possible_date, max_value=max_possible_date
)
end_date = st.sidebar.date_input(
    "End Date", max_possible_date, min_value=min_possible_date, max_value=max_possible_date
)

if start_date > end_date:
    st.sidebar.error("Start date must be on or before the end date.")
    st.stop()

unique_services = sorted(df["service_name"].dropna().unique())
selected_services = st.sidebar.multiselect(
    "Service Types (leave empty to show all)",
    options=unique_services,
    default=[],
)

selected_status = st.sidebar.radio("Request Status", ["All", "Open", "Closed"], horizontal=True)

# 3. Apply Filters to DataFrame
filtered_df = df[
    (df["request_date"] >= pd.to_datetime(start_date))
    & (df["request_date"] <= pd.to_datetime(end_date))
]

if selected_services:
    filtered_df = filtered_df[filtered_df["service_name"].isin(selected_services)]

if selected_status != "All":
    filtered_df = filtered_df[filtered_df["status"] == selected_status]

st.caption(f"Showing requests from **{start_date:%B %d, %Y}** through **{end_date:%B %d, %Y}**.")

# 4. Summary Metrics
st.subheader("📊 Summary Metrics")
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

total_requests = len(filtered_df)
metric_col1.metric("Total Requests", f"{total_requests:,}")
metric_col2.metric("Service Types", f"{filtered_df['service_name'].nunique():,}")
metric_col3.metric("ZIP Codes", f"{filtered_df['zipcode'].dropna().nunique():,}")

if total_requests > 0:
    closed_pct = (filtered_df["status"] == "Closed").mean() * 100
    metric_col4.metric("Resolution Rate (% Closed)", f"{closed_pct:.1f}%")
else:
    metric_col4.metric("Resolution Rate (% Closed)", "N/A")

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# 5. Visualizations
st.subheader("📈 Visualizations")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### Top 10 Service Types")
    top_services = filtered_df["service_name"].value_counts().head(10).sort_values()
    fig1, ax1 = plt.subplots(figsize=(6, 4.5))
    top_services.plot(kind="barh", color="skyblue", edgecolor="black", ax=ax1)
    ax1.set_title("Most Common 311 Request Types")
    ax1.set_xlabel("Number of Requests")
    ax1.set_ylabel("Service Type")
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

with col_chart2:
    st.markdown("#### Top 10 ZIP Codes")
    top_zips = filtered_df["zipcode"].dropna().value_counts().head(10).sort_values()
    fig2, ax2 = plt.subplots(figsize=(6, 4.5))
    top_zips.plot(kind="barh", color="salmon", edgecolor="black", ax=ax2)
    ax2.set_title("ZIP Codes with the Most 311 Requests")
    ax2.set_xlabel("Number of Requests")
    ax2.set_ylabel("ZIP Code")
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

st.markdown("#### Requests over Time")
requests_by_day = filtered_df.groupby("request_date").size()
fig3, ax3 = plt.subplots(figsize=(12, 4))
ax3.plot(requests_by_day.index, requests_by_day.values, color="teal", alpha=0.35, label="Daily requests")
ax3.plot(
    requests_by_day.index,
    requests_by_day.rolling(7, min_periods=1).mean().values,
    color="teal",
    linewidth=2,
    label="7-day average",
)
ax3.set_title("Daily 311 Requests")
ax3.set_xlabel("Request Date")
ax3.set_ylabel("Number of Requests")
ax3.grid(True, linestyle="--", alpha=0.5)
ax3.legend()
fig3.tight_layout()
st.pyplot(fig3)
plt.close(fig3)

col_chart4, col_chart5 = st.columns(2)

with col_chart4:
    st.markdown("#### Requests by Day of the Week")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_weekday = filtered_df["request_date"].dt.day_name().value_counts().reindex(day_order, fill_value=0)
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    by_weekday.plot(kind="bar", color="mediumpurple", edgecolor="black", ax=ax4)
    ax4.set_title("When Are Requests Submitted?")
    ax4.set_xlabel("Day of the Week")
    ax4.set_ylabel("Number of Requests")
    ax4.tick_params(axis="x", rotation=45)
    fig4.tight_layout()
    st.pyplot(fig4)
    plt.close(fig4)

with col_chart5:
    st.markdown("#### Open vs. Closed Requests")
    status_counts = filtered_df["status"].value_counts()
    fig5, ax5 = plt.subplots(figsize=(6, 4))
    status_colors = {"Closed": "seagreen", "Open": "coral"}
    status_counts.plot(
        kind="bar",
        color=[status_colors.get(s, "gray") for s in status_counts.index],
        edgecolor="black",
        ax=ax5,
    )
    ax5.set_title("Request Status")
    ax5.set_xlabel("Status")
    ax5.set_ylabel("Number of Requests")
    ax5.tick_params(axis="x", rotation=0)
    fig5.tight_layout()
    st.pyplot(fig5)
    plt.close(fig5)

# 6. Geographic View
st.subheader("🗺️ Where Requests Are Located")
MAP_SAMPLE_SIZE = 5000
map_df = filtered_df[["lat", "lon"]].dropna()
if len(map_df) > MAP_SAMPLE_SIZE:
    map_df = map_df.sample(MAP_SAMPLE_SIZE, random_state=42)
    st.caption(f"Showing a random sample of {MAP_SAMPLE_SIZE:,} of {len(filtered_df):,} requests for faster loading.")
st.map(map_df, latitude="lat", longitude="lon", size=20)

st.caption("Data source: 311 service request data, reduced to 2025 requests for this dashboard.")
