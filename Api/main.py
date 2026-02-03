#Importing necessary libraries
import os
import sys
from fastapi import FastAPI, Query, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Data.models import * #Importing necessary database functions from Data\models.py
load_dotenv()

#Creating FastAPI app instance
app = FastAPI(
    title="US treasury data",
    version="1.0.0",
    description="Application Programming Interface for Average rate of US securities"
)
#Setting up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#Setting up API security
API_KEY_NAME = "API_KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
API_KEY = os.getenv("API_KEY")

#Validate API key
async def validate_key(api_key: str = Security(api_key_header)):
    """Validate the provided API key against the expected key from environment variable."""
    expected_api_key = os.getenv("API_KEY") #Retrieving expected API key from environment variable
    print(f"DEBUG: Key from header: {api_key}, Key from env: {expected_api_key}")

    if expected_api_key is None or api_key != expected_api_key: #If API key is invalid, raise HTTPException
        raise HTTPException(status_code=401, detail="Invalid API Key") #Error messgae
    return api_key #Return valid API key

#For testing if the monitor.py works as expected
#@app.get("/crash")
#async def trigger_crash():
    # This sends a 'Kill' signal to the process running the API
    #os.kill(os.getpid(), signal.SIGTERM)

@app.on_event("startup") #When the application starts up
async def startup_event():
    await create_db_pool() #Make a connection pool to the database

@app.on_event("shutdown")
async def shutdown_event(): #When the application shuts down
    await close_db_pool() #Close the database connection pool

@app.get("/") #Root endpoint
async def root():
    return {"message": "Average Rate US Treasury API is running"} #Message on display

@app.get("/health")
async def health_check():
    return{"status":"healthy"} #Health check endpoint

@app.get("/records", dependencies=[Depends(validate_key)]) #/records endpoint wit API key dependency
async def all_records(
    db_connection = Depends(get_conn),
    page: int = Query(1, ge=1), #Page num query parameter
    size: int = Query(50, ge=1, le=100), #Page size 50 , less than or equal to 100
    all_records: bool = Query(False, alias="all"), #All records query parameter
):
    skip_amount = (page - 1) * size #Offset calculation
    if all_records: #Get all records if all_records is true
        records = await fetch_all_records(conn=db_connection)
        return {"Record": records}
    else:
        records = await fetch_all_records(conn=db_connection, limit=size, offset=skip_amount) #Fetch records with limit and offset
        results = {"Record": records, "page": page, "size": size, "offset": skip_amount}
    return results

@app.get("/records/record_count", dependencies=[Depends(validate_key)]) #/records/record_count endpoint with API key dependency
async def total_records(
    db_connection = Depends(get_conn) #Dependency
):
    total_count = await fetch_total_records(conn=db_connection) #Fetch total count
    result = {"Record_count" : total_count} #result
    return result #display result

@app.get("/records/latest", dependencies=[Depends(validate_key)]) #/records/latest endpoint with API key dependency
async def latest_record(
    db_connection = Depends(get_conn) #Database dependency
):
    record = await fetch_latest_record(conn=db_connection) #Fetch latest_record
    result = {"Record" : record} #result

    return result #display result

@app.get("/records/types", dependencies=[Depends(validate_key)]) #/records/types endpoint with API key dependency
async def get_security_types(
    db_connection = Depends(get_conn) #Database dependency
):
    record = await fetch_by_type(conn=db_connection) #fetch by type
    result = {"Security_type_desc": record} #result
    return result #display result

@app.get("/records/by-date" , dependencies=[Depends(validate_key)]) #/records/by-date endpoint with API key dependency
async def get_records_date(
    db_connection = Depends(get_conn), #DB dependency
    year: Optional[int] = Query(None, description="Filter date by year(e.g YYYY)"), #Year query parameter
    month: Optional[int] = Query(None, description="Filter date by month (1-12); 1 -> January, 2 -> Febuary.... 12 -> December"), #Month query parameter
    day: Optional[int] = Query(None, description="Filter date by day (1-31)") #Day query parameter
):
    record = await fetch_by_date(conn=db_connection, year=year, month=month , day=day) #reult with parsed parameter
    return {"Record" : record} #display result

@app.get("/records/by-security-type/" , dependencies=[Depends(validate_key)]) #/records/by-security-type/ endpoint with API key dependency
async def get_records_by_security_type(
    db_connection = Depends(get_conn), #DB dependency
    security_type: str = Query(..., description="Filter by security type description i.e security_type_desc") #Security type query parameter
):
    records = await fetch_by_security_type(
        conn=db_connection,
        security_type=security_type
    )
    results = {"Record" : records} #result
    return results #display result

@app.get("/records/by-security-type-and-date", dependencies=[Depends(validate_key)])  #/records/by-security-type-and-date endpoint with API key dependency
async def get_records_by_security_type_and_date(
    db_connection = Depends(get_conn),
    security_type: str = Query(..., description="Filter by security type description"), #Security type query parameter
    year: Optional[int] = Query(None, description="Filter date by year (e.g YYYY)"),  #Year query parameter
    month: Optional[int] = Query(None, description="Filter date by month (1-12)"), #Month query paramtre
    day: Optional[int] = Query(None, description="Filter date by day (1-31)") #Day query parameter
):
    records = await fetch_by_security_type(conn=db_connection, security_type=security_type) #Function call to fetch records by security type

    if year or month or day: #If any date filter is provided
        filtered = []
        for record in records:
            record_date = record.get("record_date")
            if record_date:
               r_year = record_date.year #Extract year from record date
               r_month = record_date.month #Extract month from record date
               r_day = record_date.day #Extract day from record date
               if (year is None or r_year == year) and \
                   (month is None or r_month == month) and \
                   (day is None or r_day == day):
                    filtered.append(record) #Append matching record to filtered list
        records = filtered #Record to be displayed
    return {"Record": records} #Display result