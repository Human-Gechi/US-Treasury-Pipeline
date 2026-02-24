# Importing necessary libraries
import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Logs.logs import db_logger

load_dotenv()  # Load env. variables
from sqlalchemy import DDL, event
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from Data.models import Records

db_url = os.getenv("DB_URL")  # get db url
db_pool = None  # Defining db_pool
db_engine = None  # Defining db_engine


async def connect_to_db():  # Function to create a database pool
    """Create a database connection pool using SQLAlchemy's async engine.

    This function initializes the connection pool with the specified database URL and configuration settings.
    It should be called during application startup to establish the connection before any database operations are performed.
    """
    try:
        global db_pool, db_engine
        db_engine = create_async_engine(
            db_url, echo=True, pool_size=10, max_overflow=20
        )  # Create an async engine with the given db url and pool settings
        db_pool = async_sessionmaker(
            db_engine, expire_on_commit=False, class_=AsyncSession
        )
        db_logger.info(
            "Database pool created successfully"
        )  # Log message if db pool created successfully
    except Exception as e:
        db_logger.error(f"Failed to create database pool: {e}")
        raise e


async def close_db_pool():  # Function to close the database pool
    """Close the connection to databse pool.

    This should be called during application shutdown to ensure all connections are properly closed and resources are released.
    """
    global db_pool, db_engine
    if db_engine is not None:
        await db_engine.dispose()  # Close all connections in the pool
        db_logger.info("Database pool closed.")


async def create_tables():  # Create tables
    """Create tables in the database based on defined schemas.

    This function should be called once during application startup to ensure the necessary tables are created before any data operations are performed.

    """
    try:
        global db_pool  # Use db_pool
        if db_pool is None:
            raise Exception(
                "DB pool not initialized. Call connect_db_pool() "
            )  # If no connection made error
        # Acquire connection and execute table creation query
        async with db_pool.begin() as session:
            await session.run_sync(
                Records.metadata.create_all
            )  # Create tables based on the defined models
            index = DDL(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_records ON avg_us_securities_2001_present (record_date, security_type_desc, security_desc);"
            )  # Create unique index to prevent duplicate records
            event.listen(Records.__table__, "after_create", index)
        db_logger.info("Table created successfully")  # log message
    except Exception as e:
        db_logger.info(f"Table not created : {e}")


async def insert_data(rows, batch_size=1000):
    """
    Insert data into the database in batches with retry logic to handle errors and conflicts.

    Parameters:

        rows: List of tuples representing rows to be inserted into the database
        batch_size: Size of each batch to be inserted

    """
    global db_pool, db_engine
    if db_pool is None:
        raise Exception("DB pool not initialized. Call connect_to_db() first.")

    if not rows:
        db_logger.warning("No rows to insert - empty list")
        return {"total_inserted": 0, "total_skipped": 0}

    total_inserted = 0
    total_skipped = 0

    try:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]

            max_retries = 5
            base_delay = 1

            for attempt in range(1, max_retries + 1):
                try:
                    async with db_engine.begin() as connection:
                        for row in batch:
                            stmt = (
                                pg_insert(Records)
                                .values(
                                    record_date=row[0],
                                    security_type_desc=row[1],
                                    security_desc=row[2],
                                    avg_interest_rate_amt=row[3],
                                )
                                .on_conflict_do_nothing(
                                    index_elements=[
                                        "record_date",
                                        "security_type_desc",
                                        "security_desc",
                                    ]
                                )
                                .returning(Records.record_id)
                            )

                        result = await connection.execute(stmt)
                        inserted_row = result.fetchone()

                        if inserted_row:
                            total_inserted += 1
                        else:
                            total_skipped += 1

                        db_logger.info(
                            f"Batch: {total_inserted} inserted, {total_skipped} skipped"
                        )
                    break
                except Exception as e:
                    if attempt == max_retries:
                        db_logger.error(
                            f"DB insertion failed after {max_retries} attempts: {e}"
                        )
                    else:
                        backoff = base_delay * (2 ** (attempt - 1))
                        db_logger.warning(
                            f"DB insertion failed (attempt {attempt}/{max_retries}), retrying in {backoff}s: {e}"
                        )
                        await asyncio.sleep(backoff)

    except Exception as e:
        db_logger.error(f"DB insertion failed: {e}")
        db_logger.error(f"Exception type: {type(e)}")

    db_logger.info(
        f"Final results: {total_inserted} inserted, {total_skipped} skipped due to conflicts"
    )
    return {"total_inserted": total_inserted, "total_skipped": total_skipped}


# Call the functions to create tables and connect to db
async def main():
    await connect_to_db()


if __name__ == "__main__":
    asyncio.run(main())  # run main()
