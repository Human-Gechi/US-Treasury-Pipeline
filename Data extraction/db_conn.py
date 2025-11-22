import sys
import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError
from psycopg2.errors import InvalidAuthorizationSpecification
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from Logs.logs import db_logger

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require"
    )
except OperationalError as e:
    db_logger.info("Failed to connect to DB")
finally:
    db_logger.info("Database connection successful")
cursor = conn.cursor()

def create_tables():
    table_query=(
        """
        CREATE TABLE us_treasury_securities(
        record_date DATE,
        security_type_description VARCHAR(100) CHECK(security_type_description IN('Marketable','Non-marketable','Interest-bearing Debt')),
        security_description VARCHAR(100),
        avg_interest_rate_amt 
        )
        """
    )