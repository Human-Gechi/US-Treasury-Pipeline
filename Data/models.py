import asyncpg
import os
import sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from Logs.logs import db_logger
load_dotenv()
db_url = os.getenv("DATABASE_URL")

db_pool = None

async def create_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
            db_logger.info("Database pool created successfully.")
        except Exception as e:
            db_logger.error(f"Failed to create database pool: {e}")
            raise e

async def close_db_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        db_logger.info("Database pool closed.")
        db_pool = None

async def get_conn():
    if db_pool is None:
        await create_db_pool()
    try:
        async with db_pool.acquire() as connection:
            yield connection
    except Exception as e:
        db_logger.error(f"Failed to acquire connection from pool: {e}")
        raise e

async def fetch_all_records(conn, limit: int, offset: int) ->dict:

    rows = await conn.fetch("""
        SELECT *
        FROM avg_us_securities_2001_present
        ORDER BY record_id ASC
        LIMIT $1 OFFSET $2 
        
    """, limit, offset)

    return [dict(row) for row in rows]

async def fetch_latest_record(conn) -> list[dict]:

    rows = await conn.fetchrow("""
        SELECT *
        FROM avg_us_securities_2001_present
        ORDER BY record_id DESC
        LIMIT 1
    """)

    return rows

async def fetch_total_records(conn) -> int:
    rows = await conn.fetchrow(
        """
        SELECT COUNT(*) as total_records
        FROM 
        avg_us_securities_2001_present ;
        """
    )
    return rows

async def fetch_by_security_type(conn, security_type: str) -> list[dict]:
    security_type = security_type.strip()

    rows = await conn.fetch("""
        SELECT * 
        FROM avg_us_securities_2001_present 
        WHERE security_type_desc = $1
        ORDER BY record_id ASC
    """, security_type)

    return [dict(row) for row in rows]
async def fetch_by_date(conn, year=None, month=None, day=None) -> list[dict]:

    query_parts = [
        "SELECT record_date, security_type_desc, security_desc, avg_interest_rate_amt",
        "FROM avg_us_securities_2001_present",
        "WHERE 1=1"
    ]
    params = []
    param_index = 1

    if year is not None:
        query_parts.append(f" AND record_year = ${param_index}")
        params.append(int(year))
        param_index += 1

    if month is not None:
        query_parts.append(f" AND EXTRACT(MONTH FROM record_date) = ${param_index}")
        params.append(int(month))
        param_index += 1

    if day is not None:
        query_parts.append(f" AND EXTRACT(DAY FROM record_date) = ${param_index}")
        params.append(int(day))
        param_index += 1

    query_parts.append("ORDER BY record_date DESC")

    query = " ".join(query_parts)

    rows = await conn.fetch(query, *params)

    return [dict(row) for row in rows]

async def fetch_by_type(conn):
    rows = await conn.fetch("""
        SELECT DISTINCT security_type_desc 
        FROM avg_us_securities_2001_present
        ORDER BY security_type_desc
    """)
    return [row[0] for row in rows]
