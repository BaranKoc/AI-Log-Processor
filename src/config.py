import os

_DEFAULT_DB_PATH: str = os.getenv("LOG_PROCESSOR_DB", "data/logs.db")
_DEFAULT_LOGS_DIR: str = os.getenv("LOG_PROCESSOR_LOGS_DIR", "logs")

# Production SQLite database path. Override via LOG_PROCESSOR_DB env var.
# Example: $env:LOG_PROCESSOR_DB = "data/other.db"  (PowerShell)
DB_PATH: str = _DEFAULT_DB_PATH

# Directory watched for incoming JSON log files. Override via LOG_PROCESSOR_LOGS_DIR env var.
LOGS_DIR: str = _DEFAULT_LOGS_DIR


def set_db_path(path: str) -> None:
    """Override DB_PATH at runtime — used by tests to inject a temp DB."""
    global DB_PATH
    DB_PATH = path


def set_logs_dir(path: str) -> None:
    """Override LOGS_DIR at runtime — used by tests to inject a temp directory."""
    global LOGS_DIR
    LOGS_DIR = path


def restore_defaults() -> None:
    """Reset DB_PATH and LOGS_DIR back to their original defaults."""
    global DB_PATH, LOGS_DIR
    DB_PATH = _DEFAULT_DB_PATH
    LOGS_DIR = _DEFAULT_LOGS_DIR
