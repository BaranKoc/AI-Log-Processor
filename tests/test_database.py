from datetime import datetime
import pytest
from src.schema import LogEntry
from src.database import init_db, insert_log, get_recent_logs

@pytest.fixture
async def db_path(tmp_path):
    """Creates a temporary SQLite database for each test."""
    path = tmp_path / "test_logs.db"
    await init_db(str(path))
    return str(path)


class TestDatabaseInit:
    """Tests that the database initializes correctly."""

    async def test_init_creates_db_file(self, tmp_path):
        path = tmp_path / "new.db"
        await init_db(str(path))
        assert path.exists()

    async def test_init_is_idempotent(self, tmp_path):
        path = tmp_path / "new.db"
        await init_db(str(path))
        await init_db(str(path))  # should not raise


class TestInsertLog:
    """Tests that logs are inserted into the database."""

    async def test_insert_single_log(self, db_path):
        log = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message="Test log",
            source="test",
        )
        await insert_log(db_path, log)
        logs = await get_recent_logs(db_path, limit=10)
        assert len(logs) == 1
        assert logs[0]["message"] == "Test log"

    async def test_insert_multiple_logs(self, db_path):
        for i in range(5):
            log = LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Log entry {i}",
                source="test",
            )
            await insert_log(db_path, log)
        logs = await get_recent_logs(db_path, limit=10)
        assert len(logs) == 5


class TestGetRecentLogs:
    """Tests the query for recent logs."""

    async def test_returns_empty_when_no_logs(self, db_path):
        logs = await get_recent_logs(db_path, limit=10)
        assert logs == []

    async def test_respects_limit(self, db_path):
        for i in range(10):
            log = LogEntry(
                timestamp=datetime.now(),
                level="WARN",
                message=f"Log {i}",
                source="test",
            )
            await insert_log(db_path, log)
        logs = await get_recent_logs(db_path, limit=5)
        assert len(logs) == 5

    async def test_returns_most_recent_first(self, db_path):
        for i in range(3):
            log = LogEntry(
                timestamp=datetime(2026, 4, 3, 12, i, 0),
                level="INFO",
                message=f"Log {i}",
                source="test",
            )
            await insert_log(db_path, log)
        logs = await get_recent_logs(db_path, limit=10)
        assert logs[0]["message"] == "Log 2"
        assert logs[2]["message"] == "Log 0"
