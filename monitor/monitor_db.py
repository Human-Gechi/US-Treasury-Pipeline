import asyncio
import os
import sys

from sqlalchemy import DDL, event

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import APIHealthCheck
from log import db_logger


async def create_tables():
    """Function to create tables in the database"""
    try:
        from data.db_conn import close_db_pool, connect_to_db

        await connect_to_db()

        from data.db_conn import db_engine

        print("Database pool created for table creation.")

        if db_engine is None:
            raise Exception("db_engine not initialized")

        # Create tables from schemas and create unique index after table creation
        async with db_engine.begin() as conn:
            await conn.run_sync(
                APIHealthCheck.metadata.create_all,
                tables=[APIHealthCheck.metadata.tables["api_health_checks"]],
            )  # Create only the API_health_checks table

            # Create unique index
            index = DDL(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_checks ON api_health_checks (checked_at, status_code, status_message);"
            )  # Create unique index to prevent duplicate records
            event.listen(APIHealthCheck.__table__, "after_create", index)

        print("Table created successfully")
    except Exception as e:
        print(f"Table was not created: {e}")
    finally:
        await close_db_pool()


async def main():
    await create_tables()


if __name__ == "__main__":
    asyncio.run(main())
