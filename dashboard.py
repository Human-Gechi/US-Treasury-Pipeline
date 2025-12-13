import streamlit as st
import requests
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from Logs.logs import streamlit_logger

load_dotenv()

BASE_API_URL = "https://us-treasury-pipeline.onrender.com"
API_KEY = st.secrets["API_KEY"]
HEADERS = {"API_KEY": API_KEY}

st.title("Average US Securities Dashboard")

def request_json(url, params=None, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        streamlit_logger.error(f"Request failed: {e}", exc_info=True)
        st.error(f"Network error calling API: {e}")
        return None
    if resp.status_code >= 500:
        streamlit_logger.error(f"Server error {resp.status_code} for {url}: {resp.text}")
        st.error(f"Server error {resp.status_code}. Check backend logs.")
        return None
    if resp.status_code >= 400:
        streamlit_logger.error(f"API returned {resp.status_code} for {url}: {resp.text}")
        st.error(f"API error {resp.status_code}: {resp.text}")
        return None
    try:
        return resp.json()
    except Exception as e:
        streamlit_logger.error(f"Invalid JSON from {url}: {e}; body={resp.text}", exc_info=True)
        st.error("Invalid JSON response from API.")
        return None

@st.cache_data
def fetch_security_types():
    payload = request_json(f"{BASE_API_URL}/records/types")
    if not payload:
        return []
    return payload.get("Security_type_desc", []) if isinstance(payload, dict) else []

@st.cache_data
def fetch_records_for_type(security_type):
    payload = request_json(f"{BASE_API_URL}/records/by-security-type", params={"security_type": security_type})
    if not payload:
        return []
    return payload.get("Record", payload) if isinstance(payload, dict) else payload

@st.cache_data
def get_latest_records():
    payload = request_json(f"{BASE_API_URL}/records/latest")
    if payload is None:
        return pd.DataFrame()
    return pd.DataFrame(payload)

def total_count():
    payload = request_json(f"{BASE_API_URL}/records/record_count")
    if not payload:
        return
    total_records = payload.get("Record_count", {}).get("total_records")
    if total_records is not None:
        st.metric(label="Record Count", value=total_records)
        streamlit_logger.info("Displayed record count card successfully.")

def display_latest():
    df = get_latest_records()
    st.subheader("Latest Record")
    if df.empty:
        st.write("No latest records found.")
    else:
        st.dataframe(df, width=700, height=245)

def card_display():
    types = fetch_security_types()
    if not types:
        st.info("No security types available.")
        return
    counts = {}
    for t in types:
        recs = fetch_records_for_type(t) or []
        counts[t] = len(recs) if isinstance(recs, list) else 0
    per_row = 3
    rows = (len(types) + per_row - 1) // per_row
    idx = 0
    for _ in range(rows):
        cols = st.columns(per_row)
        for col in cols:
            if idx >= len(types):
                break
            t = types[idx]
            with col:
                st.metric(label=t, value=counts.get(t, 0))
            idx += 1

def line_graph_filtered():
    st.subheader("Average Securities Trends")
    types = fetch_security_types()
    if not types:
        st.info("No security types available.")
        return
    selected_types = st.multiselect("Select Security Types to Compare", options=types, default=types[:1])
    if not selected_types:
        st.info("Select at least one security type.")
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        year_opt = st.selectbox("Year (optional)", options=["All"] + list(range(2001, 2100)), index=0)
    with col2:
        month_opt = st.selectbox("Month (optional)", options=["All"] + list(range(1, 13)), index=0)
    with col3:
        day_opt = st.selectbox("Day (optional)", options=["All"] + list(range(1, 32)), index=0)


        all_data = []
        for security_type in selected_types:

            records = fetch_records_for_type(security_type) or []
            for rec in records:
                rec["security_type"] = security_type
                all_data.append(rec)

        if not all_data:
            st.info("No records found for selected types.")
            return

        df = pd.DataFrame(all_data)
        if "record_date" not in df.columns or "avg_interest_rate_amt" not in df.columns:
            st.dataframe(df)
            return

        df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")
        df["avg_interest_rate_amt"] = pd.to_numeric(df["avg_interest_rate_amt"]*100, errors="coerce")
        df = df.dropna(subset=["record_date", "avg_interest_rate_amt"])

        if year_opt != "All":
                df = df[df["record_date"].dt.year == int(year_opt)]
        if month_opt != "All":
                df = df[df["record_date"].dt.month == int(month_opt)]
        if day_opt != "All":
                df = df[df["record_date"].dt.day == int(day_opt)]
        if df.empty:
            st.info("No data to plot.")
            return

        df_pivot = df.pivot_table(
            index="record_date",
            columns="security_type",
            values="avg_interest_rate_amt",
            aggfunc="mean"
        ).sort_index()
        st.session_state["line_chart_df"] = df_pivot


    if st.session_state.get("line_chart_df") is not None:
        st.subheader("Persisted Chart")
        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X('date', title='Month'),
                y=alt.Y('value', title='Average Interest Rate')
            )
            .properties(
                width=600,
                height=400,
                title="Interest Rate Over Time"
            )
        )

        st.altair_chart(st.session_state["line_chart_df"], chart, use_container_width=False)

def render_dashboard():
    col1, col2 = st.columns([1, 3])
    with col1:
        total_count()
    with col2:
        card_display()
    line_graph_filtered()
    display_latest()
render_dashboard()
