#Importing necessary libraries
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
from Logs.logs import streamlit_logger

load_dotenv()

BASE_API_URL = "https://us-treasury-pipeline.onrender.com" #Deployed url on render
API_KEY = st.secrets["API_KEY"] #Api key from secets.toml
HEADERS = {"API_KEY": API_KEY} #Appending API__KEY as header in URL

st.title("Average US Securities Dashboard") #Streamlit dashboard Name

def request_json(url, params=None, timeout=50): #Function to make a request to url
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout) #Make a request
    except requests.exceptions.RequestException as e: #Exceptions if any
        streamlit_logger.error(f"Request failed: {e}", exc_info=True) #Error message for the log file
        st.error(f"Network error calling API: {e}") #Displayed error on streamlit dashboard
        return None
    if resp.status_code >= 500: #Error message for a 500 status_Code
        streamlit_logger.error(f"Server error {resp.status_code} for {url}: {resp.text}") #Log file error message
        st.error(f"Server error {resp.status_code}. Check backend logs.") #Displayed error message on streamlit
        return None
    if resp.status_code >= 400: #400 status_code error
        streamlit_logger.error(f"API returned {resp.status_code} for {url}: {resp.text}") #Log file error message
        st.error(f"API error {resp.status_code}: {resp.text}") #Displayed error message on streamlit
        return None
    try:
        return resp.json() #Get Json dat
    except Exception as e: #Error when accessing Json data
        streamlit_logger.error(f"Invalid JSON from {url}: {e}; body={resp.text}", exc_info=True) #Log file error
        st.error("Invalid JSON response from API.") #Streamlit dahsboard error
        return None

@st.cache_data #Caching data so data can be stored in cache doesn't affect the API, Database causing connection issues
def fetch_security_types():
    payload = request_json(f"{BASE_API_URL}/records/types") #Call the API endpoint
    if not payload:
        return []
    return payload.get("Security_type_desc", []) if isinstance(payload, dict) else []

@st.cache_data #Caching data so data can be stored in cache doesn't affect the API, Database causing connection issues
def fetch_records_for_type(security_type): #Function to fetch records for a particular security type
    payload = request_json(f"{BASE_API_URL}/records/by-security-type", params={"security_type": security_type})
    if not payload:
        return []
    return payload.get("Record", payload) if isinstance(payload, dict) else payload  #Make a request to the endpoint if output is a dictionary else retrun whatever is seen

def get_latest_records(): #Function to get latest records
    payload = request_json(f"{BASE_API_URL}/records/latest") #Make a request to the latest record endpoint
    if payload is None: #If no payload i.e is no data
        return pd.DataFrame() #Return empty dataframe if no payload
    return pd.DataFrame(payload) #Return the payload as a dataframe

def total_count(): #Function to get total record count
    payload = request_json(f"{BASE_API_URL}/records/record_count") #Make a request to the record_count endpoint
    if not payload: #If no payload
        return #Return nothing
    total_records = payload.get("Record_count", {}).get("total_records") #Get total record
    if total_records is not None: #If the record was gotten
        st.metric(label="Record Count", value=total_records) #Display total record count in a metric card
        streamlit_logger.info("Displayed record count card successfully.") #Log file message

def display_latest(): #Function to display latest record
    df = get_latest_records() #Get latest record dataframe
    st.subheader("Latest Record") #Subheader for latest record
    if df.empty: #If datafram is empty;
        st.write("No latest records found.") #Display this message
    else:
        st.dataframe(df, width=700, height=215) #Display the dataframe with width and height

def card_display():#Display cards for each security type with count of records
    types = fetch_security_types() #Fetch function making request to get security types
    if not types: #If no security types;
        st.info("No security types available.") #Display this message on
        return #Return nothing
    counts = {} #Dictionary to hold security types and their counts
    for t in types: #For each security type
        recs = fetch_records_for_type(t) or [] #Fetch records for that security type
        counts[t] = len(recs) if isinstance(recs, list) else 0 #Count each record for a particular security type
    per_row = 3 #Number of cards per row
    rows = (len(types) + per_row - 1) // per_row #Calculating the number of rows needed to display the count of each card
    idx = 0 #Index to keep track of current security type
    for _ in range(rows):
        cols = st.columns(per_row) #Create columns for each row
        for col in cols:
            if idx >= len(types):#Break if number of types > types of security types
                break #Break
            t = types[idx] #Get the security type at the current index
            with col:
                st.metric(label=t, value=counts.get(t, 0)) #Display the security type and its count in a metric card
            idx += 1 #Fetch te next Security type

def line_graph_filtered(): #Line grapgh for the security types
    st.subheader("Average Securities Trends") #Sub header
    types = fetch_security_types() #Fetching security types
    if not types: #If no security type available
        st.info("No security types available.") #Streamlit error message
        return
    selected_types = st.multiselect("Select Security Types to Compare", options=types, default=types[:1]) #Selecting security types with only one selecting at a particular time[:1]
    if not selected_types: #If no security type is selected
        st.info("Select at least one security type.") #Streamlit error message
        return
    col1, col2, col3 = st.columns(3) #3 columns to display year, day, month
    with col1:
        year_opt = st.selectbox("Year (optional)", options=["All"] + list(range(2001, 2100)), index=0)
    with col2:
        month_opt = st.selectbox("Month (optional)", options=["All"] + list(range(1, 13)), index=0)
    with col3:
        day_opt = st.selectbox("Day (optional)", options=["All"] + list(range(1, 32)), index=0)

        all_data = [] #List of data in the endpoint
        for security_type in selected_types: #For each security type selected

            records = fetch_records_for_type(security_type) or [] #Fetch the record
            for rec in records:
                rec["security_type"] = security_type
                all_data.append(rec) #Append record foreach security type to a list to hold data

        if not all_data: #If no data found.
            st.info("No records found for selected types.")
            return

        df = pd.DataFrame(all_data) #Convert all_data list to a dataframe
        if "record_date" not in df.columns or "avg_interest_rate_amt" not in df.columns:
            st.dataframe(df)
            return

        df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce") #Convert to datetim
        df["avg_interest_rate_amt"] = pd.to_numeric((df["avg_interest_rate_amt"]*100).round(2), errors="coerce") #Convert to numeric
        df = df.dropna(subset=["record_date", "avg_interest_rate_amt"])#Drop null values in the columns if nay

        if year_opt != "All": #If year = ALL
                df = df[df["record_date"].dt.year == int(year_opt)]
        if month_opt != "All":
                df = df[df["record_date"].dt.month == int(month_opt)]
        if day_opt != "All":
                df = df[df["record_date"].dt.day == int(day_opt)]
        if df.empty:
            st.info("No data to plot.")
            return

        #Convert df into pivot table
        df_pivot = df.pivot_table(
            index="record_date",
            columns="security_type",
            values="avg_interest_rate_amt",
            aggfunc="mean"
        ).sort_index()
        st.session_state["line_chart_df"] = df_pivot


    if st.session_state.get("line_chart_df") is not None:
        st.subheader("Persisted Chart")
        st.line_chart(st.session_state["line_chart_df"], width=700, height=300, use_container_width=False) #Line graph

#Function for dashboard
def render_dashboard():
    col1, col2 = st.columns([1, 3])
    with col1:
        total_count()
    with col2:
        card_display()
    line_graph_filtered()
    display_latest()
render_dashboard()
