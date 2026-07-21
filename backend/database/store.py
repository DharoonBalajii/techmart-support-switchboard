"""SQLite persistence for users, auth sessions, and conversation memory."""
from __future__ import annotations

import json
import sqlite3
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.config import get_settings
from core.security import hash_password, new_id, new_token, verify_password

SESSION_TTL_DAYS = 30

_DB_PATH = Path(get_settings().database_url)
if not _DB_PATH.is_absolute():
    import os
    if os.environ.get("VERCEL"):
        _DB_PATH = Path("/tmp") / _DB_PATH.name
    else:
        _DB_PATH = Path(__file__).resolve().parent.parent / _DB_PATH


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                verified INTEGER DEFAULT 0
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS email_verification_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agents TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_auth_user ON auth_sessions(user_id)")
        
        # Migration for pre-existing DBs created before user_id or verified existed.
        cols = {row["name"] for row in c.execute("PRAGMA table_info(messages)")}
        if "user_id" not in cols:
            c.execute("ALTER TABLE messages ADD COLUMN user_id TEXT")
            
        user_cols = {row["name"] for row in c.execute("PRAGMA table_info(users)")}
        if "verified" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ---------------------------------------------------------------- users --
class EmailTakenError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def _user_out(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
        "verified": bool(row["verified"]) if "verified" in row.keys() else False,
    }


def create_user(name: str, email: str, password: str) -> dict:
    email = email.strip().lower()
    with _conn() as c:
        existing = c.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise EmailTakenError(email)
        user_id = new_id()
        c.execute(
            "INSERT INTO users (id, name, email, password_hash, created_at, verified) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name.strip(), email, hash_password(password), _iso(_now()), 0),
        )
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user_out(row)


def authenticate(email: str, password: str) -> dict:
    email = email.strip().lower()
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        raise InvalidCredentialsError()
    return _user_out(row)


def get_user_by_id(user_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user_out(row) if row else None


# ----------------------------------------------------------- auth tokens --
def create_auth_session(user_id: str) -> tuple[str, str]:
    token = new_token()
    now = _now()
    expires = now + timedelta(days=SESSION_TTL_DAYS)
    with _conn() as c:
        c.execute(
            "INSERT INTO auth_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, _iso(now), _iso(expires)),
        )
    return token, _iso(expires)


def get_user_for_token(token: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM auth_sessions WHERE token = ?", (token,)
        ).fetchone()
        if not row:
            return None
        if datetime.fromisoformat(row["expires_at"]) < _now():
            c.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
            return None
    return get_user_by_id(row["user_id"])


def delete_auth_session(token: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))


# --------------------------------------------------------- conversations --
def add_message(
    session_id: str,
    role: str,
    content: str,
    agents: list[str] | None = None,
    user_id: str | None = None,
) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO messages (session_id, user_id, role, content, agents, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, user_id, role, content, json.dumps(agents or []), _iso(_now())),
        )


def get_history(session_id: str, limit: int = 40) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content, agents, created_at FROM messages "
            "WHERE session_id = ? ORDER BY id ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [
        {
            "role": r["role"],
            "content": r["content"],
            "agents": json.loads(r["agents"] if r["agents"] else "[]"),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def llm_history(session_id: str, limit: int = 12) -> list[dict]:
    """History shaped for the LLM (role/content only)."""
    return [
        {"role": t["role"], "content": t["content"]}
        for t in get_history(session_id, limit)
    ]
