import os
import psycopg2
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
from Logs.logs import db_logger

def make_connection():
    conn = None  # Initialize the variable
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
    except Exception as e:
        db_logger.info(f"An error occurred: {e}")
    else:
        db_logger.info("Connection successful")

    return conn

def create_tables():
    conn = make_connection()
    cursor = conn.cursor()
    try:
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
    except Exception as e:
        db_logger.info("Table and schema were not created")
    else:
        db_logger.info("Table and schema created successfully")
    cursor.execute(create_table_query)
