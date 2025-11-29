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

async def connect_to_db():
    try:
        conn = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
        db_logger.info("Connection to the Database was successful")
        await conn.close()
    except Exception as e:
        db_logger.info("Connection to db failed")


async def insert_data(conn, rows, batch_size=200):
    conn = await connect_to_db()
    try:
        insertion = """
            INSERT INTO us_treasury_securities (
                record_date, 
                security_type_desc, 
                security_desc, 
                avg_interest_rate_amt
            ) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
        """

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            await conn.executemany(insertion, batch)
            total_inserted += len(batch)

        conn.commit()
        return total_inserted

    except Exception as e:
        db_logger.error(f"DB insertion failed: {e}")

    finally:
        await conn.close()


async def fetch_all_records():
    conn = await connect_to_db()
    rows = await conn.fetch("""
        SELECT record_date, security_type_desc, security_desc, avg_interest_rate_amt
        FROM us_treasury_securities
        ORDER BY record_date DESC
    """)
    await conn.close()
    return rows


async def fetch_latest_record():
    conn = await connect_to_db()
    row = await conn.fetchrow("""
        SELECT record_date, security_type_desc, security_desc, avg_interest_rate_amt
        FROM us_treasury_securities
        ORDER BY record_date DESC
        LIMIT 1
    """)
    await conn.close()
    return row


async def fetch_by_date(year=None, month=None, day=None):
    conn = await connect_to_db()

    query = """
        SELECT record_date, security_type_desc, security_desc, avg_interest_rate_amt
        FROM us_treasury_securities
        WHERE 1=1
    """

    params = []

    if year:
        query += " AND EXTRACT(YEAR FROM record_date) = $1"
        params.append(int(year))

    if month:
        query += f" AND EXTRACT(MONTH FROM record_date) = ${len(params)+1}"
        params.append(int(month))

    if day:
        query += f" AND EXTRACT(DAY FROM record_date) = ${len(params)+1}"
        params.append(int(day))

    query += " ORDER BY record_date DESC"

    rows = await conn.fetch(query, *params)
    await conn.close()
    return rows


async def fetch_by_security_type(security_type: str):
    conn = await connect_to_db()
    rows = await conn.fetch("""
        SELECT record_date, security_desc, avg_interest_rate_amt
        FROM treasury_records
        WHERE LOWER(security_type_desc) = LOWER($1)
        ORDER BY record_date DESC
    """, security_type)
    await conn.close()
    return rows
