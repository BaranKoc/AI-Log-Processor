from datetime import datetime
import pytest
import src.config as config
from src.schema import LogEntry
from src.database import init_db, insert_log, get_recent_logs


@pytest.fixture
async def setup_db(tmp_path):
    """Points config to a temp DB, initializes it, restores default after test."""
    config.set_db_path(str(tmp_path / "test_logs.db"))
    await init_db()
    yield
    config.set_db_path("data/logs.db")


class TestDatabaseInit:
    """Tests that the database initializes correctly."""

    async def test_init_creates_db_file(self, tmp_path):
        path = tmp_path / "new.db"
        config.set_db_path(str(path))
        await init_db()
        assert path.exists()
        config.set_db_path("data/logs.db")

    async def test_init_is_idempotent(self, tmp_path):
        path = tmp_path / "new.db"
        config.set_db_path(str(path))
        await init_db()
        await init_db()  # should not raise
        config.set_db_path("data/logs.db")


class TestInsertLog:
    """Tests that logs are inserted into the database."""

    async def test_insert_single_log(self, setup_db):
        log = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message="Test log",
            source="test",
        )
        await insert_log(log)
        logs = await get_recent_logs(limit=10)
        assert len(logs) == 1
        assert logs[0]["message"] == "Test log"

    async def test_insert_multiple_logs(self, setup_db):
        for i in range(5):
            log = LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Log entry {i}",
                source="test",
            )
            await insert_log(log)
        logs = await get_recent_logs(limit=10)
        assert len(logs) == 5


class TestGetRecentLogs:
    """Tests the query for recent logs."""

    async def test_returns_empty_when_no_logs(self, setup_db):
        logs = await get_recent_logs(limit=10)
        assert logs == []

    async def test_respects_limit(self, setup_db):
        for i in range(10):
            log = LogEntry(
                timestamp=datetime.now(),
                level="WARN",
                message=f"Log {i}",
                source="test",
            )
            await insert_log(log)
        logs = await get_recent_logs(limit=5)
        assert len(logs) == 5

    async def test_returns_most_recent_first(self, setup_db):
        for i in range(3):
            log = LogEntry(
                timestamp=datetime(2026, 4, 3, 12, i, 0),
                level="INFO",
                message=f"Log {i}",
                source="test",
            )
            await insert_log(log)
        logs = await get_recent_logs(limit=10)
        assert logs[0]["message"] == "Log 2"
        assert logs[2]["message"] == "Log 0"
