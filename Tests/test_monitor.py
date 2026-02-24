import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Monitor.monitor as monitor_script
import Monitor.monitor_db as monitor


class TestMonitorDB:
    @pytest.mark.asyncio
    async def test_create_tables(self) -> None:
        """Test the create_tables function."""
        try:
            await monitor.create_tables()
            # No exceptions raised == table was created successfully
        except Exception as e:
            pytest.fail(f"Table creation failed: {e}")

    @pytest.mark.asyncio
    async def test_run_monitor_cycle(self) -> None:
        "Test the run monitor_cycle function."
        try:
            await monitor_script.run_monitor_cycle()
            # No exceptions raised == table was created successfully
        except Exception as e:
            pytest.fail(f"Monitor cycle failes: {e}")
