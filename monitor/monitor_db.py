#IMporting necessary libraries
import os
import asyncpg
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
from Logs.logs import db_logger

db_url = os.getenv("DATABASE_URL") #DB url frmo .env file
db_pool = None
async def make_connection():
    """Create and  the database."""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5) #Create a connection pool
        db_logger.info("Database pool created.") #Log message

async def create_tables(conn): #Create tables in the database
    global db_pool
    if db_pool is None:
        await make_connection()
        db_logger.info("Database pool created for table creation.") #Log message

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
    """ #SQL query to create table and index
    try:
        async with db_pool.acquire() as conn: #Acquire a connection from the pool
            await conn.execute(create_table_query) #Execute the create table query
    except Exception as e:
        db_logger.info("Table and schema were not created") #Error log
    else:
        db_logger.info("Table and schema created successfully") #Success log


