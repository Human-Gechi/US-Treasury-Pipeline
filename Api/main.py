# Importing necessary libraries
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Data.service as service  # Importing necessary database functions from Data\models.py
from Data.db_conn import (  # Importing necessary database connection functions from Data\db_conn.py
    close_db_pool,
    connect_to_db,
)
from Logs.logs import api_logger  # Importing logger for API logs

load_dotenv()

# Creating FastAPI app instance
app = FastAPI(
    title="US treasury data",
    version="1.0.0",
    description="Application Programming Interface for Average rate of US securities",
)
# Setting up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://us-treasury-pipeline-rijzjnbzowvw8ydra7f5uq.streamlit.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Setting up API security
API_KEY_NAME = "API_KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
API_KEY = os.getenv("API_KEY")


async def validate_key(api_key: str = Security(api_key_header)):
    """Validate the provided API key against the expected key from environment variable."""

    expected_api_key = os.getenv(
        "API_KEY"
    )  # Retrieving expected API key from environment variable
    print(
        True if api_key == expected_api_key else False
    )  # Print true if API key is valid, false otherwise

    if (
        expected_api_key is None or api_key != expected_api_key
    ):  # If API key is invalid, raise HTTPException
        raise HTTPException(status_code=401, detail="Invalid API Key")  # Error messgae
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan function to manage database connections on startup and shutdown."""

    try:
        api_logger.info("Starting database connection...")
        await connect_to_db()
        api_logger.info("Database connected successfully")
    except Exception as e:
        api_logger.error(f"Failed to connect to database: {e}")
        raise
    yield
    try:
        api_logger.info("Closing database pool...")
        await close_db_pool()
        api_logger.info("Database pool closed")
    except Exception as e:
        api_logger.error(f"Error closing database: {e}")


app = FastAPI(
    lifespan=lifespan
)  # Creating FastAPI app instance with lifespan for database connection management


@app.get("/")  # Root endpoint
async def root():
    """Root endpoint"""
    return {"message": "Average Rate US Treasury API is running"}  # Message on display


@app.get("/health")
async def health_check():
    """API health endpoint"""

    return {"status": "healthy"}


@app.get(
    "/records", dependencies=[Depends(validate_key)]
)  # /records endpoint wit API key dependency
async def all_records(
    db_connection=Depends(service.get_db),  # DB dependency
    page: int = Query(1, ge=1),  # Page num query parameter
    size: int = Query(50, ge=1, le=100),  # Page size: 50; less than or equal to 100
    all_records: bool = Query(False, alias="all"),  # All records query parameter
):
    """Fetch records with pagination or all records if specified."""

    skip_amount = (page - 1) * size  # Offset calculation
    if all_records:  # Get all records if all_records is true
        records = await service.fetch_all_records(
            Session=db_connection, limit=1000, offset=100
        )
        return {"Record": records}
    else:
        records = await service.fetch_all_records(
            Session=db_connection, limit=size, offset=skip_amount
        )  # Fetch records with limit and offset
        results = {"Record": records, "page": page, "size": size, "offset": skip_amount}
    return results


@app.get(
    "/records/record_count", dependencies=[Depends(validate_key)]
)  # /records/record_count endpoint with API key dependency
async def total_records(
    db_connection=Depends(service.get_db),  # DB Dependency
):
    """Fetch total record count."""
    total_count = await service.fetch_total_records(
        Session=db_connection
    )  # Fetch total count
    result = {"Record_count": total_count}
    return result  # display result


@app.get(
    "/records/latest", dependencies=[Depends(validate_key)]
)  # /records/latest endpoint with API key dependency
async def latest_record(
    db_connection=Depends(service.get_db),  # Database dependency
):
    """Fetch latest record"""
    record = await service.fetch_latest_record(
        Session=db_connection
    )  # Fetch latest_record
    result = {"Record": record}  # result

    return result  # display result


@app.get(
    "/records/types", dependencies=[Depends(validate_key)]
)  # /records/types endpoint with API key dependency
async def get_records_by_security_types(
    db_connection=Depends(service.get_db),  # Database dependency
):
    record = await service.fetch_by_type(Session=db_connection)  # fetch by type
    result = {"Security_type_desc": record}  # result
    return result  # display result


@app.get(
    "/records/by-date", dependencies=[Depends(validate_key)]
)  # /records/by-date endpoint with API key dependency
async def get_records_by_date(
    db_connection=Depends(service.get_db),
    year: Optional[int] = Query(None, description="Filter date by year(e.g YYYY)"),
    month: Optional[int] = Query(
        None,
        description="Filter date by month (1-12); 1 -> January, 2 -> Febuary.... 12 -> December",
    ),
    day: Optional[int] = Query(None, description="Filter date by day (1-31)"),
):
    """fetch records by date filters."""
    record = await service.fetch_by_date(
        Session=db_connection, year=year, month=month, day=day
    )
    return {"Record": record}  # display result


@app.get(
    "/records/by-security-type/", dependencies=[Depends(validate_key)]
)  # /records/by-security-type/ endpoint with API key dependency
async def get_records_by_security_type(
    db_connection=Depends(service.get_db),
    security_type: str = Query(
        ..., description="Filter by security type description i.e security_type_desc"
    ),  # Security type query parameter
):
    """Fetch records by security type."""
    records = await service.fetch_by_security_type(
        Session=db_connection, security_type=security_type
    )
    results = {"Record": records}  # result
    return results  # display result


@app.get(
    "/records/by-security-type-and-date", dependencies=[Depends(validate_key)]
)  # /records/by-security-type-and-date endpoint with API key dependency
async def get_records_by_security_type_and_date(
    db_connection=Depends(service.get_db),
    security_type: str = Query(..., description="Filter by security type description"),
    year: Optional[int] = Query(None, description="Filter date by year (e.g YYYY)"),
    month: Optional[int] = Query(None, description="Filter date by month (1-12)"),
    day: Optional[int] = Query(None, description="Filter date by day (1-31)"),
):
    """Fetch records by security type and optional date filter."""

    records = await service.fetch_by_security_type(
        Session=db_connection, security_type=security_type
    )

    if year or month or day:  # If date filter is provided
        filtered = []
        for record in records:
            record_date = record.get("record_date")
            if record_date:
                r_year = record_date.year  # Extract year from record date
                r_month = record_date.month  # Extract month from record date
                r_day = record_date.day  # Extract day from record date
                if (
                    (year is None or r_year == year)
                    and (month is None or r_month == month)
                    and (day is None or r_day == day)
                ):
                    filtered.append(record)  # Append matching record to filtered list
        records = filtered  # Record to be displayed
    return {"Record": records}  # Display result
