import os

# Production SQLite database path. Override via LOG_PROCESSOR_DB env var.
# Example: $env:LOG_PROCESSOR_DB = "data/other.db"  (PowerShell)
DB_PATH: str = os.getenv("LOG_PROCESSOR_DB", "data/logs.db")

# Directory watched for incoming JSON log files. Override via LOG_PROCESSOR_LOGS_DIR env var.
LOGS_DIR: str = os.getenv("LOG_PROCESSOR_LOGS_DIR", "logs")


def set_db_path(path: str) -> None:
    """Override DB_PATH at runtime — used by tests to inject a temp DB."""
    global DB_PATH
    DB_PATH = path


def set_logs_dir(path: str) -> None:
    """Override LOGS_DIR at runtime — used by tests to inject a temp directory."""
    global LOGS_DIR
    LOGS_DIR = path
