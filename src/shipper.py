import asyncio

from src.database import insert_log
from src.schema import LogEntry


async def ship_log(log: LogEntry) -> None:
    """Simulates shipping a single log entry to the database with latency."""
    if not log:
        return
    await asyncio.sleep(0.1)  # Simulate network latency
    await insert_log(log)


async def ship_batch(logs: list[LogEntry]) -> None:
    """Ships multiple log entries concurrently."""
    if not logs:
        return
    async with asyncio.TaskGroup() as tg:
        for log in logs:
            tg.create_task(ship_log(log))