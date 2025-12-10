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

def fetch_api_data(endpoint):
    url = f"{BASE_API_URL}{endpoint}"
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

st.sidebar.header("URL Navigation")
endpoint_choice = st.sidebar.selectbox(
    "Choose an API endpoint:",
    ['records', 'records/record_count', 'records/latest', 'records/types']
)
st.subheader(f"Data for: {endpoint_choice}")

data = fetch_api_data(endpoint_choice)

