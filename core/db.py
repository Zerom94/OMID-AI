"""OMID AI — SQLite Database Wrapper"""
import sqlite3
import os
import threading
from contextlib import contextmanager
from datetime import datetime

class MemoryStore:
    def __init__(self, db_path: str = "/sdcard/omid-ai/omid_ai.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active'
                    );
                    CREATE TABLE IF NOT EXISTS agent_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS security_scans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT NOT NULL,
                        scan_type TEXT NOT NULL,
                        results TEXT NOT NULL,
                        report_path TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_message(self, role: str, content: str):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))

    def get_recent_messages(self, limit: int = 10):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def set_preferences(self, pref_dict: dict):
        with self._lock:
            with self.get_connection() as conn:
                for key, value in pref_dict.items():
                    conn.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)", (key, value))

    def get_preferences(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM preferences").fetchall()
            return {row["key"]: row["value"] for row in rows}

    def reserve_project(self, name: str, path: str) -> int:
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.execute("INSERT INTO projects (name, path) VALUES (?, ?)", (name, path))
                return cursor.lastrowid

    def log_event(self, agent: str, event_type: str, data: dict):
        import json
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("INSERT INTO agent_logs (agent, event_type, data) VALUES (?, ?, ?)", (agent, event_type, json.dumps(data, ensure_ascii=False)))

    def save_security_scan(self, target: str, scan_type: str, results: dict, report_path: str = None):
        import json
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("INSERT INTO security_scans (target, scan_type, results, report_path) VALUES (?, ?, ?, ?)", (target, scan_type, json.dumps(results, ensure_ascii=False), report_path))

_db_instance = None
def get_db() -> MemoryStore:
    global _db_instance
    if _db_instance is None:
        _db_instance = MemoryStore()
    return _db_instance
