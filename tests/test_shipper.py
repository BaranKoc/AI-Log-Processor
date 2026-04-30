import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest
import src.config as config

from src.database import init_db, get_recent_logs
from src.schema import LogEntry
from src.shipper import ship_log, ship_batch


@pytest.fixture
async def setup_db(tmp_path):
    config.set_db_path(str(tmp_path / "test_shipper.db"))
    await init_db()
    yield
    config.set_db_path("data/logs.db")


def make_log(message: str = "test", level: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime.now(),
        level=level,
        message=message,
        source="test-service",
    )


class TestShipLog:
    """Tests that ship_log inserts a single log into the DB."""

    async def test_ships_single_log(self, setup_db):
        log = make_log("single entry")
        await ship_log(log)
        rows = await get_recent_logs(limit=10)
        assert len(rows) == 1
        assert rows[0]["message"] == "single entry"

    async def test_ships_log_with_each_level(self, setup_db):
        for level in ["INFO", "WARN", "ERROR"]:
            await ship_log(make_log(f"{level} msg", level))
        rows = await get_recent_logs(limit=10)
        assert len(rows) == 3

    async def test_simulates_latency(self, setup_db):
        with patch("src.shipper.asyncio.sleep", return_value=None) as mock_sleep:
            await ship_log(make_log())
            mock_sleep.assert_called_once()


class TestShipBatch:
    """Tests that ship_batch ships multiple logs concurrently."""

    async def test_batch_ships_all_logs(self, setup_db):
        logs = [make_log(f"batch log {i}") for i in range(5)]
        await ship_batch(logs)
        rows = await get_recent_logs(limit=10)
        assert len(rows) == 5

    async def test_batch_empty_list(self, setup_db):
        await ship_batch([])
        rows = await get_recent_logs(limit=10)
        assert len(rows) == 0

    async def test_batch_is_concurrent_not_sequential(self, setup_db):
        logs = [make_log(f"concurrent {i}") for i in range(5)]
        start = asyncio.get_event_loop().time()
        await ship_batch(logs)
        elapsed = asyncio.get_event_loop().time() - start
        # 5 logs with ~0.1s simulated latency each should complete
        # well under 1s if concurrent (would be ~0.5s if sequential)
        assert elapsed < 0.5
