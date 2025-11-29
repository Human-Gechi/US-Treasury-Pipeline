import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from Logs.logs import db_logger
load_dotenv()

db_url = os.getenv("DATABASE_URL")
db_pool = None
db_url = os.getenv("DATABASE_URL")

async def connect_to_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
        db_logger.info("Connection to Database was successful")
    return db_pool

async def create_tables():
    try:
        global db_pool
        if db_pool is None:
            raise Exception("DB pool not initialized. Call connect_to_db() ")

        table_query = """
            CREATE TABLE IF NOT EXISTS avg_us_securities_2001_present (
                record_id SERIAL PRIMARY KEY,
                record_date DATE,
                record_year INT GENERATED ALWAYS AS (COALESCE(EXTRACT(YEAR FROM record_date)::INT, 0)) STORED,
                security_type_desc VARCHAR(100) CHECK(security_type_desc IN('Marketable','Non-marketable','Interest-bearing Debt')),
                security_desc VARCHAR(100),
                avg_interest_rate_amt DECIMAL(7,5) DEFAULT 0
            )
        """
        async with db_pool.acquire() as conn:
            await conn.execute(table_query)
            db_logger.info("Table created successfully")
    except Exception as e:
        db_logger.info(f"Table not created : {e}")

async def insert_data(conn, rows, batch_size=200):
    global db_pool
    if db_pool is None:
        raise Exception("DB pool not initialized. Call connect_to_db() first.")
    total_inserted = 0
    try:
        insertion = """
            INSERT INTO avg_us_securities_2001_present(
                record_date, 
                security_type_desc, 
                security_desc, 
                avg_interest_rate_amt
            ) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING
        """

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]

            async with db_pool.acquire() as conn:
                for row in batch:
                    await conn.execute(insertion, *row)
                total_inserted += len(batch)

        return total_inserted

    except Exception as e:
        db_logger.error(f"DB insertion failed: {e}")


async def main():
    await connect_to_db()
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main())

