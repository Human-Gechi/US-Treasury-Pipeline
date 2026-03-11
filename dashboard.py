# Importing necessary libraries
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from log import streamlit_logger

load_dotenv()

BASE_API_URL = "https://us-treasury-pipeline.onrender.com"  # Deployed url on render
API_KEY = st.secrets["API_KEY"]
HEADERS = {"API_KEY": API_KEY}

st.title("Average US Securities Dashboard")


def request_json(url, params=None, timeout=50):
    """Function to make a request to the API and return the JSON response."""
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)  # Make a request
    except requests.exceptions.RequestException as e:
        streamlit_logger.error(f"Request failed: {e}", exc_info=True)
        st.error(f"Network error calling API: {e}")
        return None

    if resp.status_code >= 500:  # Error message for a 500 status_Code
        streamlit_logger.error(f"Server error {resp.status_code} for {url}: {resp.text}")
        st.error(f"Server error {resp.status_code}. Check backend logs.")  # Displayed error message on streamlit
        return None

    if resp.status_code >= 400:  # 400 status_code error
        streamlit_logger.error(f"API returned {resp.status_code} for {url}: {resp.text}")
        st.error(f"API error {resp.status_code}: {resp.text}")
        return None
    try:
        return resp.json()  # Get Json dat
    except Exception as e:  # Error when accessing Json data
        streamlit_logger.error(f"Invalid JSON from {url}: {e}; body={resp.text}", exc_info=True)  # Log file error
        st.error("Invalid JSON response from API.")  # Streamlit dashboard error
        return None


@st.cache_data  # Caching data so data can be stored in cache doesn't affect the API, Database causing connection issues
def fetch_security_types():
    payload = request_json(f"{BASE_API_URL}/records/types")  # Call the API endpoint

    if not payload:
        return []
    return payload.get("Security_type_desc", []) if isinstance(payload, dict) else []


@st.cache_data  # Caching data so data can be stored in cache doesn't affect the API, Database causing connection issues
def fetch_records_for_type(security_type: str):
    """Function to fetch records for a particular security type."""
    payload = request_json(
        f"{BASE_API_URL}/records/by-security-type",
        params={"security_type": security_type},
    )

    if not payload:
        return []

    if isinstance(payload, list):
        return payload


def fetch_latest_records():
    """Function to get the latest record for each security type."""
    payload = request_json(f"{BASE_API_URL}/records/latest")
    if not payload:
        return pd.DataFrame()  # Return empty dataframe if no payload

    if isinstance(payload, dict):
        return pd.DataFrame([payload])  # wrap single record from dict to list
    if isinstance(payload, list):
        return pd.DataFrame(payload)

    return pd.DataFrame()


def total_count():
    """Function to get the total count of records and display it in a metric card."""
    payload = request_json(f"{BASE_API_URL}/records/record-count")
    if not payload:  # If no payload
        return  # Return nothing

    if isinstance(payload, dict):
        total_records = payload.get("Record_count")

        if total_records is None and "Records" in payload:
            total_records = len(payload.get("Records", []))
    else:
        total_records = None

    if total_records is not None:
        st.metric(label="Record Count", value=total_records)
        streamlit_logger.info("Displayed record count card successfully.")


def display_latest():
    """Function to display latest record."""
    st.subheader("Latest Record")
    df = fetch_latest_records()

    if df.empty:
        st.error("No latest record available.")
        return

    latest = df.iloc[0]

    vertical_df = (
        latest.rename_axis("field").reset_index(name="value")  # index name  # two columns: field{Key}, value
    )
    st.dataframe(vertical_df, width="stretch", hide_index=True)
    streamlit_logger.info("Displayed LATEST Record sucessfully")


def card_display():
    """Function to display the count of each security type in a card format."""
    types = fetch_security_types()
    if not types:
        st.error("No security types available.")  # Display this message on
        return  # Return nothing
    counts = {}  # Dictionary to hold security types and their counts
    for t in types:  # For each security type
        recs = fetch_records_for_type(t) or []  # Fetch records for that security type
        counts[t] = len(recs) if isinstance(recs, list) else 0  # Count each record for a particular security type
    per_row = 3  # Number of cards per row
    rows = (
        len(types) + per_row - 1
    ) // per_row  # Calculating the number of rows needed to display the count of each card
    idx = 0  # Index to keep track of current security type
    for _ in range(rows):
        cols = st.columns(per_row)  # Create columns for each row
        for col in cols:
            if idx >= len(types):  # Break if number of types > types of security types
                break  # Break
            t = types[idx]  # Get the security type at the current index
            with col:
                st.metric(label=t, value=counts.get(t, 0))  # Display the security type and its count in a metric card
            idx += 1  # Fetch te next Security type


def line_graph_filtered():
    """Function to display a line graph of average interest rates over time for selected security types and date filters."""
    st.subheader("Average Securities Trends")  # Sub header
    types = fetch_security_types()  # Fetching security types
    if not types:
        st.error("No security types available.")  # Streamlit error message
        return
    selected_types = st.multiselect(
        "Select Security Types to Compare", options=types, default=types[:1]
    )  # Selecting security types with only one selecting at a particular time
    if not selected_types:  # If no security type is selected
        st.info("Select at least one security type.")
        return

    col1, col2, col3 = st.columns(3)  # 3 columns to display year, day, month
    with col1:
        year_opt = st.selectbox(
            "Year (optional)",
            options=["All"] + list(range(2001, 2100)),
            index=0,
        )
    with col2:
        month_opt = st.selectbox("Month (optional)", options=["All"] + list(range(1, 13)), index=0)
    with col3:
        day_opt = st.selectbox("Day (optional)", options=["All"] + list(range(1, 32)), index=0)

    all_data = []  # List of data in the endpoint
    for security_type in selected_types:  # For each security type selected
        records = fetch_records_for_type(security_type) or []  # Fetch the record
        for rec in records:
            rec["security_type"] = security_type
            all_data.append(rec)  # Append record foreach security type to a list to hold data

    if not all_data:  # If no data found.
        st.error("No records found for selected types.")
        return

    df = pd.DataFrame(all_data)  # Convert all_data list to a dataframe
    if "record_date" not in df.columns or "avg_interest_rate_amt" not in df.columns:
        st.dataframe(df)
        return

    df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")  # Convert to datetime
    df["avg_interest_rate_amt"] = pd.to_numeric(
        (df["avg_interest_rate_amt"] * 100).round(2), errors="coerce"
    )  # Convert to numeric
    df = df.dropna(subset=["record_date", "avg_interest_rate_amt"])  # Drop null values in the columns if any

    if year_opt != "All":  # If year = ALL
        df = df[df["record_date"].dt.year == int(year_opt)]
    if month_opt != "All":
        df = df[df["record_date"].dt.month == int(month_opt)]
    if day_opt != "All":
        df = df[df["record_date"].dt.day == int(day_opt)]

    if df.empty:
        st.info("No data to plot.")
        return

    # Convert df into pivot table
    df_pivot = df.pivot_table(
        index="record_date",
        columns="security_type",
        values="avg_interest_rate_amt",
        aggfunc="mean",
    ).sort_index()

    st.subheader("% Securities Average Interest Rate Over Time")  # Subheader for line graph
    st.line_chart(df_pivot, width=700, height=400)


def render_dashboard():
    """Function to render the dashboard by calling the necessary functions"""
    col1, col2 = st.columns([1, 3])
    with col1:
        total_count()
    with col2:
        card_display()
    line_graph_filtered()
    display_latest()


render_dashboard()
