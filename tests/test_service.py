import os
import sys
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data.db_conn as db_conn
import data.service as service


@pytest.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture to provide a database session for tests."""
    gen = service.get_db()
    db_session = await anext(gen)
    try:
        yield db_session
    finally:
        await (
            gen.aclose()
        )  # Closes one AsyncGenerator instance, ensures database cleanup of the database session after each test.


@pytest.fixture(scope="session", autouse=True)
async def close_test_db_pool():
    """Ensure engine is disposed after all tests."""
    yield
    await db_conn.close_db_pool()  # Closes the database connection pool after all tests have completed ensuring all the resources have been removed and connections is closed.


@pytest.fixture(scope="session")
async def security_type() -> str:
    """Fixture to provide a valid security type for tests."""
    return "Interest-bearing Debt"


@pytest.fixture(scope="session")
async def date_params() -> tuple[int, int, int]:
    """Fixture to provide valid date parameters for tests."""
    return (2003, 1, 1)


class TestDataModule:
    @pytest.mark.asyncio
    async def test_connect_to_db(self, session: AsyncSession) -> None:
        """Test database connection."""
        try:
            assert isinstance(session, AsyncSession)
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.asyncio
    async def test_fetch_all_records(self, session: AsyncSession) -> None:
        """Test fetching records from DB."""
        records = await service.fetch_all_records(session, limit=10, offset=0)
        assert isinstance(records, list)
        assert all(isinstance(record, dict) for record in records)
        records.clear()

    @pytest.mark.asyncio
    async def test_fetch_latest_record(self, session: AsyncSession) -> None:
        """Test fetching the latest record from the database."""
        latest_record = await service.fetch_latest_record(session)
        assert len(latest_record) == 1
        assert isinstance(latest_record[0], dict)
        latest_record.clear()  # Clear the list after a test to free up memory

    @pytest.mark.asyncio
    async def test_fetch_total_records(self, session: AsyncSession) -> None:
        """Test fetching total record count from DB."""
        total_records = await service.fetch_total_records(session)  # Fixed function name
        assert total_records > 0
        assert isinstance(total_records, int)

    @pytest.mark.asyncio
    async def test_fetch_by_security_type(self, session: AsyncSession, security_type: str) -> None:
        """Test fetching records by security type from DB."""
        records = await service.fetch_by_security_type(session, security_type=security_type)
        assert isinstance(records, list)
        assert len(records) > 0
        assert all(record["Records"].security_type_desc == security_type for record in records)
        records.clear()

    @pytest.mark.asyncio
    async def test_fetch_by_date(self, session: AsyncSession, date_params: tuple[int, int, int]) -> None:
        """Test fetching records by date from the database."""
        records = await service.fetch_by_date(
            session,
            year=date_params[0],
            month=date_params[1],
            day=date_params[2],
        )
        assert isinstance(records, list)
        assert all(
            record["Records"].record_year == date_params[0]
            and record["Records"].record_date.month == date_params[1]
            and record["Records"].record_date.day == date_params[2]
            for record in records
        )
        records.clear()

    @pytest.mark.asyncio
    async def test_fetch_by_type(self, session: AsyncSession) -> None:
        """Test fetching unique security types from database."""
        security_types = await service.fetch_by_type(session)
        assert isinstance(security_types, list)
        assert len(security_types) > 0
        assert all(isinstance(record, str) for record in security_types)
        security_types.clear()
