import os
import asyncpg
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
from Logs.logs import db_logger

db_url = os.getenv("DATABASE_URL")
db_pool = None


async def create_tables(conn):
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
        db_logger.info("Database pool created for table creation.")

    create_table_query = """
    CREATE TABLE IF NOT EXISTS API_health_checks (
        id SERIAL PRIMARY KEY,
        checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        status_code INTEGER NOT NULL,
        status_message TEXT,
        latency_ms FLOAT NOT NULL,
        is_healthy BOOLEAN NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_checked_at 
    ON API_health_checks (checked_at);
    """
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(create_table_query)
    except Exception as e:
        db_logger.info("Table and schema were not created")
    else:
        db_logger.info("Table and schema created successfully")


