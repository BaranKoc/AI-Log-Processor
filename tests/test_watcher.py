import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

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

    def test_handler_stores_db_path_and_loop(self):
        loop = asyncio.new_event_loop()
        handler = LogFileHandler(db_path="test.db", loop=loop)
        assert handler.db_path == "test.db"
        assert handler.loop is loop
        loop.close()

    def test_on_created_triggers_for_json_file(self):
        loop = asyncio.new_event_loop()
        handler = LogFileHandler(db_path="dummy.db", loop=loop)
        event = type("Event", (), {"src_path": "/tmp/new_log.json", "is_directory": False})()
        with patch("src.watcher.asyncio.run_coroutine_threadsafe") as mock_bridge:
            handler.on_created(event)
            mock_bridge.assert_called_once()
        loop.close()

    def test_on_created_ignores_non_json_file(self):
        loop = asyncio.new_event_loop()
        handler = LogFileHandler(db_path="dummy.db", loop=loop)
        event = type("Event", (), {"src_path": "/tmp/readme.txt", "is_directory": False})()
        with patch("src.watcher.asyncio.run_coroutine_threadsafe") as mock_bridge:
            handler.on_created(event)
            mock_bridge.assert_not_called()
        loop.close()

    def test_on_created_ignores_directories(self):
        loop = asyncio.new_event_loop()
        handler = LogFileHandler(db_path="dummy.db", loop=loop)
        event = type("Event", (), {"src_path": "/tmp/subdir", "is_directory": True})()
        with patch("src.watcher.asyncio.run_coroutine_threadsafe") as mock_bridge:
            handler.on_created(event)
            mock_bridge.assert_not_called()
        loop.close()


class TestStartWatcher:
    """Tests that start_watcher creates and returns a running observer."""

    def test_watcher_starts_and_stops(self, tmp_path):
        loop = asyncio.new_event_loop()
        observer = start_watcher(str(tmp_path), "dummy.db", loop)
        assert observer.is_alive()
        observer.stop()
        observer.join(timeout=2)
        assert not observer.is_alive()
        loop.close()
