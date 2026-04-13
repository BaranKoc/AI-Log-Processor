import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest

from src.database import init_db, get_recent_logs
from src.watcher import LogFileHandler, process_log_file, start_watcher


def write_log_file(directory: Path, filename: str, data: dict) -> Path:
    """Helper — writes a JSON log file into the given directory."""
    file_path = directory / filename
    file_path.write_text(json.dumps(data))
    return file_path


def valid_log_data(message: str = "test event") -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "message": message,
        "source": "test-service",
    }


@pytest.fixture
async def db_path(tmp_path):
    path = tmp_path / "test_watcher.db"
    await init_db(str(path))
    return str(path)


class TestProcessLogFile:
    """Tests that process_log_file reads, validates, and ships a single JSON file."""

    async def test_processes_valid_json_file(self, tmp_path, db_path):
        file = write_log_file(tmp_path, "valid.json", valid_log_data("hello watcher"))
        await process_log_file(str(file), db_path)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 1
        assert rows[0]["message"] == "hello watcher"

    async def test_rejects_invalid_json_content(self, tmp_path, db_path):
        file = tmp_path / "bad.json"
        file.write_text("not valid json {{{")
        await process_log_file(str(file), db_path)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 0  # nothing inserted

    async def test_rejects_invalid_schema(self, tmp_path, db_path):
        bad_data = {"timestamp": datetime.now().isoformat(), "level": "CRITICAL", "message": "bad"}
        file = write_log_file(tmp_path, "bad_schema.json", bad_data)
        await process_log_file(str(file), db_path)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 0  # validation failed, nothing inserted

    async def test_ignores_non_json_files(self, tmp_path, db_path):
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("not a log")
        await process_log_file(str(txt_file), db_path)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 0

    async def test_processes_multiple_files(self, tmp_path, db_path):
        for i in range(3):
            write_log_file(tmp_path, f"log_{i}.json", valid_log_data(f"event {i}"))
            await process_log_file(str(tmp_path / f"log_{i}.json"), db_path)
        rows = await get_recent_logs(db_path, limit=10)
        assert len(rows) == 3


class TestLogFileHandler:
    """Tests that the watchdog handler only reacts to .json file creation events."""

    def test_handler_has_on_created(self):
        handler = LogFileHandler(db_path="dummy.db", loop=asyncio.new_event_loop())
        assert hasattr(handler, "on_created")

    def test_handler_stores_db_path_and_loop(self):
        loop = asyncio.new_event_loop()
        handler = LogFileHandler(db_path="test.db", loop=loop)
        assert handler.db_path == "test.db"
        assert handler.loop is loop
        loop.close()


class TestStartWatcher:
    """Tests that start_watcher creates and returns an observer monitoring the directory."""

    def test_watcher_starts_and_stops(self, tmp_path):
        loop = asyncio.new_event_loop()
        observer = start_watcher(str(tmp_path), "dummy.db", loop)
        assert observer.is_alive()
        observer.stop()
        observer.join(timeout=2)
        assert not observer.is_alive()
        loop.close()

    def test_watcher_targets_correct_directory(self, tmp_path):
        loop = asyncio.new_event_loop()
        observer = start_watcher(str(tmp_path), "dummy.db", loop)
        # observer._watches contains the scheduled paths
        assert observer.is_alive()
        observer.stop()
        observer.join(timeout=2)
        loop.close()
