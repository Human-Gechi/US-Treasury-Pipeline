from datetime import datetime

import pytest


@pytest.fixture
def records() -> list[tuple[datetime, str, float]]:
    """Fixture to provide sample records for testing."""
    return [
        (datetime(2024, 1, 1), "Type A", 1.5),
        (datetime(2024, 1, 2), "Type B", 2.5),
    ]


@pytest.mark.asyncio
async def test_api_insertion(records, batch_size=2) -> None:
    """Function to test the API insertion of records into the DB"""
    assert len(records) == batch_size
    assert isinstance(records, list)
    assert all(isinstance(record, tuple) for record in records)
    assert all(isinstance(record[0], datetime) for record in records)
    assert all(isinstance(record[1], str) for record in records)
    assert all(isinstance(record[2], float) for record in records)
