from src.database import insert_log
from src.schema import LogEntry
import asyncio


async def ship_log(db_path: str, log: LogEntry):
    """Simulates shipping a single log entry to the database with latency."""
    
    if not log:
        return
    
    await asyncio.sleep(0.1)  # Simulate network latency
    await insert_log(db_path, log)

async def ship_batch(db_path: str, logs: list[LogEntry]):
    """Ships multiple log entries concurrently."""

    if not logs:
        return
    
    async with asyncio.TaskGroup() as tg:
        for log in logs:
            tg.create_task(ship_log(db_path, log))