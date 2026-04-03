from datetime import datetime
import pytest
from pydantic import ValidationError
from src.schema import LogEntry

class TestLogEntryValidData:
    """Tests that valid log data passes Pydantic validation."""

    def test_valid_log_entry(self):
        log = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message="Server started successfully",
            source="auth-service",
        )
        assert log.message == "Server started successfully"
        assert log.level == "INFO"

    def test_valid_log_with_all_levels(self):
        for level in ["INFO", "WARN", "ERROR"]:
            log = LogEntry(
                timestamp=datetime.now(),
                level=level,
                message="test message",
                source="test-service",
            )
            assert log.level == level


class TestLogEntryInvalidData:
    """Tests that malformed data is rejected by Pydantic."""

    def test_missing_message_raises_error(self):
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                source="auth-service",
            )

    def test_missing_level_raises_error(self):
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp=datetime.now(),
                message="something happened",
                source="auth-service",
            )

    def test_invalid_level_raises_error(self):
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp=datetime.now(),
                level="CRITICAL",
                message="something happened",
                source="auth-service",
            )

    def test_empty_message_raises_error(self):
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="",
                source="auth-service",
            )


class TestLogEntrySerialization:
    """Tests that LogEntry can round-trip to/from dict and JSON."""

    def test_to_dict(self):
        log = LogEntry(
            timestamp=datetime(2026, 4, 3, 12, 0, 0),
            level="ERROR",
            message="Connection timeout",
            source="db-service",
        )
        data = log.model_dump()
        assert data["level"] == "ERROR"
        assert data["source"] == "db-service"

    def test_from_json_string(self):
        raw = '{"timestamp": "2026-04-03T12:00:00", "level": "INFO", "message": "OK", "source": "api"}'
        log = LogEntry.model_validate_json(raw)
        assert log.message == "OK"

    def test_from_dict(self):
        raw = {
            "timestamp": "2026-04-03T12:00:00",
            "level": "WARN",
            "message": "Disk usage high",
            "source": "monitoring",
        }
        log = LogEntry.model_validate(raw)
        assert log.level == "WARN"
