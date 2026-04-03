import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest

from src.database import init_db, get_recent_logs
from src.schema import LogEntry
from src.shipper import ship_log, ship_batch


@pytest.fixture
async def db_path(tmp_path):
    path = tmp_path / "test_shipper.db"
    await init_db(str(path))
    return str(path)


def make_log(message: str = "test", level: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime.now(),
        level=level,
        message=message,
        source="test-service",
    )


class TestShipLog:
    """Tests that ship_log inserts a single log into the DB."""

    async def test_ships_single_log(self, db_path):
        log = make_log("single entry")
        await ship_log(db_path, log)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 1
        assert rows[0]["message"] == "single entry"

    async def test_ships_log_with_each_level(self, db_path):
        for level in ["INFO", "WARN", "ERROR"]:
            await ship_log(db_path, make_log(f"{level} msg", level))
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 3

    async def test_simulates_latency(self, db_path):
        with patch("src.shipper.asyncio.sleep", return_value=None) as mock_sleep:
            await ship_log(db_path, make_log())
            mock_sleep.assert_called_once()


class TestShipBatch:
    """Tests that ship_batch ships multiple logs concurrently."""

    async def test_batch_ships_all_logs(self, db_path):
        logs = [make_log(f"batch log {i}") for i in range(5)]
        await ship_batch(db_path, logs)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 5

    async def test_batch_empty_list(self, db_path):
        await ship_batch(db_path, [])
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 0

    async def test_batch_is_concurrent_not_sequential(self, db_path):
        logs = [make_log(f"concurrent {i}") for i in range(5)]
        start = asyncio.get_event_loop().time()
        await ship_batch(db_path, logs)
        elapsed = asyncio.get_event_loop().time() - start
        # 5 logs with ~0.1s simulated latency each should complete
        # well under 1s if concurrent (would be ~0.5s if sequential)
        assert elapsed < 0.5
