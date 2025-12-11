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
                if endpoint_data["Record_count"]["total_records"]:
                    total_records = endpoint_data["Record_count"]["total_records"]
                    st.markdown("""
                        <style>
                        /* Metric value (the number) */
                        [data-testid="stMetricValue"] {
                            color: #1d4ed8;   /* strong blue */
                            font-weight: 700; /* bold for emphasis */
                            font-size: 1.8rem; /* slightly larger than default */
                        }
                        </style>
                        """, unsafe_allow_html=True)

                    st.metric(label="Record Count", value=total_records)
                    streamlit_logger.info("Displayed record count card successfully.")
            except requests.exceptions.HTTPError as e:
                streamlit_logger.error(f"HTTP Error: {e}")
                st.error(f"Authentication Error accessing {endpoint_url}: {e}")
            except requests.exceptions.RequestException as e:
                streamlit_logger.error(f"A Network Error occured: {e}")
                st.error(f"Network Error: {e}")
            except Exception as e:
                streamlit_logger.error (f"An unexpected error occurred: {e}")

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


    if "selected_types" not in st.session_state:
        st.session_state["selected_types"] = []

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

    per_row = 4
    rows = (len(types) + per_row - 1) // per_row
    idx = 0
    for _ in range(rows):
        cols = st.columns(per_row)
        for col in cols:
            if idx >= len(types):
                break
            t = types[idx]
            selected = t in st.session_state["selected_types"]
            with col:
                label = f"**{t}**" if selected else t
                st.markdown(label)
                st.metric(label="Count", value=counts.get(t, 0))

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
def render_dashboard():
        total_count()
        display_latest()
        card_display()
render_dashboard()


