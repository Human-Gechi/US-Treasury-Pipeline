#Importing necessary libraries
import asyncpg
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Logs.logs import db_logger
load_dotenv()
db_url = os.getenv("DATABASE_URL") #Database url

db_pool = None #Defining db_pool to None

async def create_db_pool(): #Function to create a database pool
    global db_pool #Use the global db_pool variable
    if db_pool is None:#If no db_pool created
        try:
            db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5) #Create a database pool
            db_logger.info("Database pool created successfully.") #Log info for successful creation
        except Exception as e: #If error occurs during creation
            db_logger.error(f"Failed to create database pool: {e}") #Log error message
            raise e

async def close_db_pool(): #Function to close the database pool
    global db_pool
    if db_pool:
        await db_pool.close()
        db_logger.info("Database pool closed.")
        db_pool = None

async def get_conn(): #Function to get a connection from the pool
    if db_pool is None: #If no db_pool created
        await create_db_pool() #Create a db_pool using the function creat_db_pool defined above
    try: #Acquire a connection from the pool
        async with db_pool.acquire() as connection:
            yield connection #Yield the connection
    except Exception as e:
        db_logger.error(f"Failed to acquire connection from pool: {e}") #Log error message if no connection made
        raise e #Raise exceptionoi

async def fetch_all_records(conn, limit: int, offset: int) ->dict: #Function to fetch all records with limit and offset
    """Fetch all records from the database with pagination i. e limit and offset."""
    rows = await conn.fetch("""
        SELECT *
        FROM avg_us_securities_2001_present
        LIMIT $1 OFFSET $2 
        
    """, limit, offset) #Execute the query with limit and offset

    return [dict(row) for row in rows] #Return rows as a list of dictionaries

async def fetch_latest_record(conn) -> list[dict]:
    """Fetch the latest record from the database."""
    rows = await conn.fetchrow("""
        SELECT *
        FROM avg_us_securities_2001_present
        ORDER BY record_date DESC
        LIMIT 1
    """)
    return rows

async def fetch_total_records(conn) -> int:
    """Fetch the total number of records in the database."""
    rows = await conn.fetchrow(
        """
        SELECT COUNT(*) as total_records
        FROM
        avg_us_securities_2001_present ;
        """
    )
    return rows #Return total number of records

async def fetch_by_security_type(conn, security_type: str) -> list[dict]:
    """Fetch records by security type."""
    security_type = security_type.strip() #Strip any leading or trrailing whitespace

    rows = await conn.fetch("""
        SELECT *
        FROM avg_us_securities_2001_present
        WHERE security_type_desc = $1
    """, security_type) #Execute the query with security type

    return [dict(row) for row in rows] #Return rows as a list of dictionaries
async def fetch_by_date(conn, year=None, month=None, day=None) -> list[dict]:
    """Fetch records in the db by date. Splitting on year, month, day"""
    query_parts = [
        "SELECT record_date, security_type_desc, security_desc, avg_interest_rate_amt",
        "FROM avg_us_securities_2001_present",
        "WHERE 1=1"
    ]
    params = [] #List to hold parameters
    param_index = 1 #Parameter index for query placeholders

    if year is not None: #If year is in the function
        query_parts.append(f" AND record_year = ${param_index}") #Append year to query parts
        params.append(int(year)) #Append year to params
        param_index += 1 #Increment param index

    if month is not None: #If month is nnot None
        query_parts.append(f" AND EXTRACT(MONTH FROM record_date) = ${param_index}") #Append month to query parts
        params.append(int(month)) #Append month to params
        param_index += 1

    if day is not None:
        query_parts.append(f" AND EXTRACT(DAY FROM record_date) = ${param_index}") #``
        params.append(int(day)) #Append day to params
        param_index += 1

    query_parts.append("ORDER BY record_date DESC") #Append order by to the query parts on the record date

    query = " ".join(query_parts) #. join the query part using space to form the final query

    rows = await conn.fetch(query, *params) #Make a connection using the final query and params for each placeholder

    return [dict(row) for row in rows] #Return rows as a list of dictionaries

async def fetch_by_type(conn):
    """Fetch unique security types from the database."""
    rows = await conn.fetch("""
        SELECT DISTINCT security_type_desc
        FROM avg_us_securities_2001_present
        ORDER BY security_type_desc
    """)
    return [row[0] for row in rows] #Return unique security types as a list
