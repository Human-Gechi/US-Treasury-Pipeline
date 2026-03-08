# Importing necessary libraries
import os
import sys
from typing import AsyncGenerator

from sqlalchemy import distinct, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data.db_conn
from data.models import Records
from logs.log import db_logger


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints - auto-initializes connection

    This function serves as a dependency for FastAPI endpoints, providing an asynchronous database session.

    It ensures that the database connection pool is initialized before yielding a session for use in endpoint handlers.
    """
    if data.db_conn.db_pool is None:
        await data.db_conn.connect_to_db()

    async with data.db_conn.db_pool() as session:
        yield session


async def fetch_all_records(Session: AsyncSession, limit: int, offset: int) -> list[dict]:
    """Fetch all records from the database with pagination.

    Parameters:
        Session: The async database session to use for the query.
        limit: The maximum number of records to return.
        offset: The number of records to skip before starting to return results.

    """
    try:
        query = select(Records).limit(limit).offset(offset)
        result = await Session.execute(query)
        rows = result.mappings().all()
        return [dict(row) for row in rows]
    except Exception as e:
        db_logger.error(f"Error fetching records: {e}")
        raise e


async def fetch_latest_record(Session: AsyncSession) -> list[dict]:
    """Fetch the latest record from the database.

    Parameters:
        Session: The async database session to use for the query.
    """
    try:
        query = select(Records).order_by(Records.record_date.desc()).limit(1)
        result = await Session.execute(query)
        rows = result.mappings().all()
        return [dict(row) for row in rows]
    except Exception as e:
        db_logger.error(f"Error fetching records: {e}")
        raise e


async def fetch_total_records(Session: AsyncSession) -> int:
    """Fetch the total number of records in the database.

    Parameters:
        Session: The async database session to use for the query.
    """
    try:
        rows = select(func.count()).select_from(Records)
        result = await Session.execute(rows)
        return result.scalars().first() or 0
    except Exception as e:
        db_logger.error(f"Error fetching records: {e}")
        raise e


async def fetch_by_security_type(Session: AsyncSession, security_type: str) -> list[dict]:
    """Fetch records by security type.

    Parameters:
        Session: The async database session to use for the query.
        security_type: The security type description to filter records by.
    """
    try:
        security_type = security_type.strip()  # Strip any leading or trailing whitespace
        query = select(Records).where(Records.security_type_desc == security_type)
        rows = await Session.execute(query)
        result = rows.mappings().all()
        return [dict(row) for row in result]
    except Exception as e:
        db_logger.error(f"Error fetching records: {e}")
        raise e


async def fetch_by_date(Session: AsyncSession, year=None, month=None, day=None):
    """Fetch records in the db by date. Splitting on year, month, day

    Parameters:
       Session: The async database session to use for the query.
       year: Optional year to filter records by (e.g., 2023).
       month: Optional month to filter records by (1-12).
       day: Optional day to filter records by (1-31).
    """
    query_parts = [
        "SELECT record_date, security_type_desc, security_desc, avg_interest_rate_amt",
        "FROM avg_us_securities_2001_present",
        "WHERE 1 = 1",
    ]
    params = {}  # List to hold parameters

    if year is not None:  # If year is in the function
        query_parts.append(
            " AND EXTRACT(YEAR FROM record_date) = :year"
        )  # Append year to query parts
        params["year"] = int(year)  # Append year to params

    if month is not None:  # If month is not None
        query_parts.append(
            " AND EXTRACT(MONTH FROM record_date) = :month"
        )  # Append month to query parts
        params["month"] = int(month)  # Append month to params

    if day is not None:
        query_parts.append(" AND EXTRACT(DAY FROM record_date) = :day")  # ``
        params["day"] = int(day)  # Append day to params

    query_parts.append(
        "ORDER BY record_date DESC"
    )  # Append order by to the query parts on the record date

    query = " ".join(query_parts)  # . join the query part using space to form the final query
    try:
        result = await Session.execute(
            text(query), params
        )  # Make a connection using the final query and params for each placeholder
        rows = result.mappings().all()
        return [dict(row) for row in rows]  # Return rows as a list of dictionaries
    except Exception as e:
        db_logger.error(f"Error fetching records by date filters: {e}")
        raise e


async def fetch_by_type(Session: AsyncSession) -> list[str]:
    """Fetch unique security types from the database.

    Parameters:
        Session: The async database session to use for the query.
    """
    query = select(distinct(Records.security_type_desc)).order_by(Records.security_type_desc)
    rows = await Session.execute(query)
    result = rows.scalars().all()
    return result
