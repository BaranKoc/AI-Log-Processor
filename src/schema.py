from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

class LogEntry(BaseModel):

    timestamp: datetime
    level: LogLevel  # Validates against the Enum LogLevel
    message: str = Field(min_length=1)  # Message must be a non-empty string
    source: str