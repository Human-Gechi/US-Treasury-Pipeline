import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from Logs.logs import streamlit_logger

load_dotenv()

BASE_API_URL = 'https://us-treasury-pipeline.onrender.com/'
API_KEY = os.getenv('API_KEY')
HEADERS = {
    'API_KEY': API_KEY
}

st.title("API Dashboard")
endpoints = ["records","records/record_count", "records/latest", "records/types", "records/by-date", "records/by-security-type"]
def fetch_api_data():
    url = f"{BASE_API_URL}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        streamlit_logger.error(f"HTTP Error: {e}")
        st.error(f"Authentication Error accessing {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        streamlit_logger.error(f"A Network Error occured: {e}")
        st.error(f"Network Error: {e}")
        return None
    except Exception as e:
        streamlit_logger.error (f"An unexpected error occurred: {e}")

def total_count():
    data = fetch_api_data()
    if data:
        endpoint_url = f"{BASE_API_URL}/records/record_count"
        try:
            response = requests.get(endpoint_url, headers=HEADERS)
            response.raise_for_status()
            endpoint_data = response.json()
            total_records = endpoint_data.get("Record_count", {}).get("total_records")
            if total_records is not None:
                st.metric(label="Record Count", value=total_records)
                streamlit_logger.info("Displayed record count card successfully.")
        except requests.exceptions.HTTPError as e:
            streamlit_logger.error(f"HTTP Error: {e}")
            st.error(f"Authentication Error accessing {endpoint_url}: {e}")
        except requests.exceptions.RequestException as e:
            streamlit_logger.error(f"A Network Error occured: {e}")
            st.error(f"Network Error: {e}")
        except Exception as e:
            streamlit_logger.error(f"An unexpected error occurred: {e}")

def display_latest():
    if st.session_state.get("latest_shown"):
        return
    data = fetch_api_data()
    if data:
        endpoint_url = f"{BASE_API_URL}/records/latest"
        try:
            response = requests.get(endpoint_url, headers=HEADERS)
            response.raise_for_status()
            endpoint_data = response.json()

            df = pd.DataFrame(endpoint_data)

            st.subheader("Latest Records")
            if df.empty:
                st.write("No latest records found.")
            else:
                st.markdown("""
                        <style>
                        .dataframe {
                            max-height: 50px; /* Set a fixed height */
                            overflow-y: auto; /* Enable vertical scrolling */
                        }
                        </style>
                        """, unsafe_allow_html=True)
            st.dataframe(df, width=325, height=250)
            st.session_state["latest_shown"] = True

        except requests.exceptions.HTTPError as e:
            streamlit_logger.error(f"HTTP Error: {e}")
            st.error(f"Authentication Error accessing {endpoint_url}: {e}")
        except requests.exceptions.RequestException as e:
            streamlit_logger.error(f"A Network Error occured: {e}")
            st.error(f"Network Error: {e}")
        except Exception as e:
            streamlit_logger.error(f"An unexpected error occured: {e}")
            st.error(f"Error displaying latest records: {e}")

def card_display():
    try:
        resp = requests.get(f"{BASE_API_URL}records/types", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        types = payload.get("Security_type_desc", []) if isinstance(payload, dict) else []
    except Exception as e:
        streamlit_logger.error(f"Failed to load security types: {e}")
        st.error("Could not load security types.")
        return

    if not types:
        st.info("No security types available.")
        return

    counts = {}
    for t in types:
        try:
            r = requests.get(
                f"{BASE_API_URL}records/by-security-type/",
                headers=HEADERS,
                params={"security_type": t},
                timeout=10,
            )
            r.raise_for_status()
            p = r.json()
            recs = p.get("Record", p) if isinstance(p, dict) else p
            counts[t] = len(recs) if isinstance(recs, list) else 0
        except Exception as e:
            streamlit_logger.error(f"Error fetching count for {t}: {e}")
            counts[t] = 0
        except requests.exceptions.HTTPError as e:
            streamlit_logger.error(f"HTTP Error: {e}")
            st.error(f"Authentication Error accessing {r}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            streamlit_logger.error(f"A Network Error occured: {e}")
            st.error(f"Network Error: {e}")
            return None

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


def security_types():
    data = fetch_api_data()
    if not data:
        return

    resp = requests.get(
        f"{BASE_API_URL}records/by-security-type/",
            headers=HEADERS,
            timeout=10,
        )
    resp.raise_for_status()
    payload = resp.json()
    endpoints = payload.get("Security_type_desc")
    for e in endpoints:
        print(e)


def line_graph_filtered():
    st.subheader("Average Securities Trends")

    try:
        resp = requests.get(f"{BASE_API_URL}records/by-security-type-and-date", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        types = payload.get("Security_type_desc", []) if isinstance(payload, dict) else []
    except Exception as e:
        streamlit_logger.error(f"Failed to load security types: {e}")
        st.error("Could not load security types.")
        return

    if not types:
        st.info("No security types available.")
        return

    selected_type = st.selectbox("Select Security Type", options=types)

    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Year (optional)", min_value=2001, max_value=2100, value=None)
    with col2:
        month = st.number_input("Month (optional)", min_value=1, max_value=12, value=None)
    with col3:
        day = st.number_input("Day (optional)", min_value=1, max_value=31, value=None)

    if st.button("Generate Graph"):
        try:
            params = {"security_type": selected_type}
            if year:
                params["year"] = year
            if month:
                params["month"] = month
            if day:
                params["day"] = day

            resp = requests.get(
                f"{BASE_API_URL}records/by-security-type-and-date",
                headers=HEADERS,
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            payload = resp.json()
            records = payload.get("Record", [])

            if records:
                df = pd.DataFrame(records)


                if "record_date" in df.columns and "avg_interest_rate_amt" in df.columns:
                    try:
                        df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")
                        df["avg_interest_rate_amt"] = pd.to_numeric(df["avg_interest_rate_amt"], errors="coerce")
                    except Exception:
                        pass

                    df = df.dropna(subset=["record_date", "avg_interest_rate_amt"])
                    df_sorted = df.sort_values(by="record_date")

                    st.line_chart(df_sorted.set_index("record_date")["avg_interest_rate_amt"])
                else:
                    st.dataframe(df)
            else:
                st.info("No records found for the selected filters.")
        except Exception as e:
            streamlit_logger.error(f"Failed to generate graph: {e}")
            st.error(f"Error: {e}")
        except requests.exceptions.HTTPError as e:
            streamlit_logger.error(f"HTTP Error: {e}")
            st.error(f"Authentication Error accessing {resp}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            streamlit_logger.error(f"A Network Error occured: {e}")
            st.error(f"Network Error: {e}")
            return None

def render_dashboard():
    col1, col2 = st.columns([1, 3])
    with col1:
        total_count()
    with col2:
        card_display()
    display_latest()
    line_graph_filtered()

render_dashboard()


