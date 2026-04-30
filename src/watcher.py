import asyncio
import json
import logging
from pathlib import Path

import src.config as config
from pydantic import ValidationError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.schema import LogEntry
from src.shipper import ship_log

logger = logging.getLogger(__name__)


# region LogFileHandler

class LogFileHandler(FileSystemEventHandler):

    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.loop = loop

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        if not event.src_path.endswith(".json"):
            return
        asyncio.run_coroutine_threadsafe(
            process_log_file(event.src_path),
            self.loop,
        )

# endregion


# region Core Functions

async def process_log_file(file_path: str) -> None:
    path = Path(file_path)
    if path.suffix != ".json":
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read/parse %s: %s", file_path, exc)
        return

    try:
        log = LogEntry(**data)
    except ValidationError as exc:
        logger.warning("Schema validation failed for %s: %s", file_path, exc)
        return

    await ship_log(log)


def start_watcher(loop: asyncio.AbstractEventLoop) -> Observer:
    handler = LogFileHandler(loop=loop)
    observer = Observer()
    observer.schedule(handler, config.LOGS_DIR, recursive=False)
    observer.start()
    return observer

# endregion
