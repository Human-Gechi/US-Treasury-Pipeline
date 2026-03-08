import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Data.db_conn import connect_to_db, create_tables, insert_data


@pytest.fixture(scope="function")
def rows():
    return [("2024-01-01", "Type A", 1.5), ("2024-01-02", "Type B", 2.5)]


async def test_connect_to_db():
    """Function to test the database connection"""
    try:
        await connect_to_db()
    except Exception as e:
        pytest.fail(f"Failed to connect to database: {e}")


async def test_create_tables():
    """Function to create tables in the database for testing"""
    try:
        await create_tables()
    except Exception as e:
        pytest.fail(f"Failed to create tables: {e}")


async def test_insert_data(rows, batch_size=2):
    try:
        await insert_data(rows, batch_size)
    except Exception as e:
        pytest.fail(f"Data insertion failed: {e}")
