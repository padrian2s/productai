"""Database connection management and migration runner for ProductAI."""

import aiosqlite
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent.parent.parent / "productai.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Run all pending migrations in order. Safe to call on every startup."""
    db = await get_db()
    try:
        # Ensure the migrations tracking table exists
        await db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                applied_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

        # Get already-applied migrations
        cursor = await db.execute("SELECT name FROM _migrations")
        applied = {row[0] for row in await cursor.fetchall()}

        # Discover and run pending migrations in sorted order
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for mf in migration_files:
            if mf.name in applied:
                continue
            sql = mf.read_text()
            await db.executescript(sql)
            await db.execute(
                "INSERT INTO _migrations (name) VALUES (?)", (mf.name,)
            )
            await db.commit()
    finally:
        await db.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
