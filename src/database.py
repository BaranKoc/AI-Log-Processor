import aiosqlite
import src.config as config
from src.schema import LogEntry


async def init_db() -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL CHECK(level IN ('INFO', 'WARN', 'ERROR')),
                message TEXT NOT NULL,
                source TEXT NOT NULL
            )
        """)
        await db.commit()


async def insert_log(log: LogEntry) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            INSERT INTO logs (timestamp, level, message, source)
            VALUES (?, ?, ?, ?)
        """, (log.timestamp.isoformat(), log.level.value, log.message, log.source))
        await db.commit()


async def get_recent_logs(limit: int = 100) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("""
            SELECT timestamp, level, message, source
            FROM logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [
            {
                "timestamp": row[0],
                "level": row[1],
                "message": row[2],
                "source": row[3],
            }
            for row in rows
        ]