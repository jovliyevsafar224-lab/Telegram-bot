"""SQLite (aiosqlite) — foydalanuvchilar va xatolar jadvali."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite
from aiogram.types import User

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT,
    first_name     TEXT,
    last_name      TEXT,
    language_code  TEXT,
    joined_at      TEXT NOT NULL,
    last_active    TEXT NOT NULL,
    requests_count INTEGER NOT NULL DEFAULT 0,
    is_banned      INTEGER NOT NULL DEFAULT 0,
    blocked_bot    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS error_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    update_id  INTEGER,
    user_id    INTEGER,
    error_type TEXT,
    message    TEXT,
    traceback  TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ago(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database ulanmagan: connect() chaqirilmagan")
        return self._conn

    async def connect(self) -> None:
        if self._conn is not None:
            return
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _scalar(self, sql: str, params: tuple = ()) -> int:
        cur = await self.conn.execute(sql, params)
        row = await cur.fetchone()
        return row[0] if row and row[0] is not None else 0

    # ---------- foydalanuvchilar ----------
    async def touch_user(self, u: User) -> tuple[bool, bool]:
        """Foydalanuvchini qo'shadi/yangilaydi. Qaytaradi: (yangi_mi, bloklanganmi)."""
        now = _now()
        cur = await self.conn.execute("SELECT is_banned FROM users WHERE user_id = ?", (u.id,))
        row = await cur.fetchone()
        if row is None:
            await self.conn.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, language_code,"
                " joined_at, last_active, requests_count) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                (u.id, u.username, u.first_name, u.last_name, u.language_code, now, now),
            )
            await self.conn.commit()
            return True, False
        await self.conn.execute(
            "UPDATE users SET username=?, first_name=?, last_name=?, language_code=?,"
            " last_active=?, requests_count=requests_count+1, blocked_bot=0 WHERE user_id=?",
            (u.username, u.first_name, u.last_name, u.language_code, now, u.id),
        )
        await self.conn.commit()
        return False, bool(row["is_banned"])

    async def get_user(self, user_id: int) -> Optional[aiosqlite.Row]:
        cur = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cur.fetchone()

    async def set_banned(self, user_id: int, banned: bool) -> bool:
        cur = await self.conn.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?", (int(banned), user_id)
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def mark_blocked(self, user_id: int) -> None:
        await self.conn.execute("UPDATE users SET blocked_bot = 1 WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def recent_users(self, limit: int = 10) -> list[aiosqlite.Row]:
        cur = await self.conn.execute(
            "SELECT * FROM users ORDER BY joined_at DESC LIMIT ?", (limit,)
        )
        return list(await cur.fetchall())

    async def all_users(self) -> list[aiosqlite.Row]:
        cur = await self.conn.execute("SELECT * FROM users ORDER BY joined_at")
        return list(await cur.fetchall())

    async def broadcast_ids(self) -> list[int]:
        cur = await self.conn.execute(
            "SELECT user_id FROM users WHERE is_banned = 0 AND blocked_bot = 0"
        )
        return [r["user_id"] for r in await cur.fetchall()]

    async def stats(self) -> dict[str, int]:
        return {
            "total": await self._scalar("SELECT COUNT(*) FROM users"),
            "new_24h": await self._scalar(
                "SELECT COUNT(*) FROM users WHERE joined_at >= ?", (_ago(24),)
            ),
            "active_24h": await self._scalar(
                "SELECT COUNT(*) FROM users WHERE last_active >= ?", (_ago(24),)
            ),
            "banned": await self._scalar("SELECT COUNT(*) FROM users WHERE is_banned = 1"),
            "blocked": await self._scalar("SELECT COUNT(*) FROM users WHERE blocked_bot = 1"),
            "errors_24h": await self._scalar(
                "SELECT COUNT(*) FROM error_logs WHERE created_at >= ?", (_ago(24),)
            ),
        }

    # ---------- xatolar ----------
    async def log_error(
        self,
        update_id: Optional[int],
        user_id: Optional[int],
        error_type: str,
        message: str,
        traceback_text: str,
    ) -> None:
        await self.conn.execute(
            "INSERT INTO error_logs (created_at, update_id, user_id, error_type, message, traceback)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (_now(), update_id, user_id, error_type, message[:1000], traceback_text[:8000]),
        )
        await self.conn.commit()

    async def recent_errors(self, limit: int = 5) -> list[aiosqlite.Row]:
        cur = await self.conn.execute(
            "SELECT * FROM error_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        return list(await cur.fetchall())
