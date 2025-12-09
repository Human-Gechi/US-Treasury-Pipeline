import os
import sys
from fastapi import FastAPI, Query, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from Data.models import *

load_dotenv()

app = FastAPI(
    title="US treasury data",
    version="1.0.0",
    description="Application Programming Interface for Average rate of US securities"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY_NAME = "API_KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
API_KEY = os.getenv("API_KEY")

async def validate_keys(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

@app.on_event("startup")
async def startup_event():
    await create_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool()

@app.get("/")
async def root():
    return {"message": "Average Rate US Treasury API is running"}

@app.get("/records", dependencies=[Depends(validate_keys)])
async def all_records(
    db_connection = Depends(get_conn),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    all_records: bool = Query(False, alias="all"),
):
    skip_amount = (page - 1) * size
    if all_records:
        records = await fetch_all_records(conn=db_connection)
        return {"Record": records}
    else:
        records = await fetch_all_records(conn=db_connection, limit=size, offset=skip_amount)
        results = {"Record": records, "page": page, "size": size, "offset": skip_amount}
    return results

@app.get("/records/record_count", dependencies=[Depends(validate_keys)])
async def total_records(
    db_connection = Depends(get_conn)
):
    total_count = await fetch_total_records(conn=db_connection)
    result = {"Record_count" : total_count}

    return result

@app.get("/records/latest", dependencies=[Depends(validate_keys)])
async def latest_record(
    db_connection = Depends(get_conn)
):
    record = await fetch_latest_record(conn=db_connection)
    result = {"Record" : record}

    return result

@app.get("/records/types", dependencies=[Depends(validate_keys)])
async def get_security_types(
    db_connection = Depends(get_conn)
):
    record = await fetch_by_type(conn=db_connection)
    result = {"Security_type_desc": record}

    return result

@app.get("/records/by-date" , dependencies=[Depends(validate_keys)])
async def get_records_date(
    db_connection = Depends(get_conn),
    year: Optional[int] = Query(None, description="Filter date by year(e.g YYYY)"),
    month: Optional[int] = Query(None, description="Filter date by month (1-12); 1-January, 2-Febuary.... 12-December"),
    day: Optional[int] = Query(None, description="Filter date by day (1-31)")
):
    record = await fetch_by_date(conn=db_connection, year=year, month=month , day=day)
    return {"Record" : record}

@app.get("/records/by-security-type/" , dependencies=[Depends(validate_keys)])
async def get_records_by_security_type(
    db_connection = Depends(get_conn),
    security_type: str = Query(..., description="Filter by security type description i.e security_type_desc")
):

    records = await fetch_by_security_type(
        conn=db_connection,
        security_type=security_type
    )
    results = {"Record" : records}
    return results
