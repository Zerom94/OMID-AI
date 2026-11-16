import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

DATA_DIR = Path(os.environ.get("OMID_DATA_DIR", "/sdcard/omid-ai"))
SRC_DIR = Path(os.environ.get("OMID_SRC_DIR", "src"))
DB_PATH = Path(os.environ.get("OMID_DB_PATH", str(DATA_DIR / "omid.db")))

MAX_HISTORY_ROWS = 500
MAX_EVENT_ROWS = 1000
PROJECT_NUMBER_OFFSET = 1000

SCHEMA = """
CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')), content TEXT NOT NULL, agent_id TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agent_states (agent_id TEXT PRIMARY KEY, status TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, entry_file TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

class Database:
    def __init__(self, path: Path | str = DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def set_preference(self, key: str, value: Any) -> None:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        with self._conn() as conn:
            conn.execute("INSERT INTO preferences (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at", (key, text, _now()))

    def get_preferences(self, limit: int = 50) -> dict[str, str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT key, value FROM preferences ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def add_message(self, role: str, content: str, agent_id: Optional[str] = None) -> None:
        with self._conn() as conn:
            conn.execute("INSERT INTO chat_history (role, content, agent_id, created_at) VALUES (?, ?, ?, ?)", (role, content, agent_id, _now()))
            conn.execute("DELETE FROM chat_history WHERE id NOT IN (SELECT id FROM chat_history ORDER BY id DESC LIMIT ?)", (MAX_HISTORY_ROWS,))

    def get_recent_messages(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT role, content, agent_id, created_at FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def set_agent_state(self, agent_id: str, status: str, detail: str = "") -> None:
        with self._conn() as conn:
            conn.execute("INSERT INTO agent_states (agent_id, status, detail, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(agent_id) DO UPDATE SET status = excluded.status, detail = excluded.detail, updated_at = excluded.updated_at", (agent_id, status, detail[:300], _now()))

    def reserve_project(self, name: str) -> int:
        with self._conn() as conn:
            cur = conn.execute("INSERT INTO projects (name, created_at) VALUES (?, ?)", (name, _now()))
            return PROJECT_NUMBER_OFFSET + int(cur.lastrowid)

    def log_event(self, event_type: str, data: Any) -> None:
        try:
            payload = json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            payload = str(data)
        with self._conn() as conn:
            conn.execute("INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)", (event_type, payload[:4000], _now()))
            conn.execute("DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT ?)", (MAX_EVENT_ROWS,))

class MemoryStore(Database):
    def save_result(self, result: Any) -> None:
        self.log_event("result", {"task_id": getattr(result, "task_id", None), "success": getattr(result, "success", None), "error": getattr(result, "error", None)})

_db: Optional[MemoryStore] = None
_db_lock = threading.Lock()

def get_db() -> MemoryStore:
    global _db
    if _db is None:
        with _db_lock:
            if _db is None:
                _db = MemoryStore()
    return _db
