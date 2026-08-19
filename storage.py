import sqlite3
import uuid
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class Database:
    def __init__(self, db_path: str = "claude_chat.db"):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    model TEXT NOT NULL,
                    effort TEXT DEFAULT 'Medium',
                    system_prompt TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    thinking TEXT DEFAULT '',
                    tokens INTEGER DEFAULT 0,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cache_read_tokens INTEGER DEFAULT 0,
                    cache_creation_tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            # Ensure columns exist for upgraded schemas
            for col, col_type in [
                ("effort", "TEXT DEFAULT 'Medium'"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            for col, col_type in [
                ("input_tokens", "INTEGER DEFAULT 0"),
                ("output_tokens", "INTEGER DEFAULT 0"),
                ("cache_read_tokens", "INTEGER DEFAULT 0"),
                ("cache_creation_tokens", "INTEGER DEFAULT 0"),
                ("cost", "REAL DEFAULT 0.0"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE messages ADD COLUMN {col} {col_type}")
                except Exception:
                    pass
            conn.commit()

    def create_session(
        self,
        title: str = "New Conversation",
        model: str = "claude-3-7-sonnet-20250219",
        effort: str = "Medium",
        system_prompt: str = ""
    ) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, model, effort, system_prompt, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, title, model, effort, system_prompt, now, now)
            )
            conn.commit()
        return session_id

    def get_sessions(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_session_settings(self, session_id: str, model: str, effort: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE sessions SET model = ?, effort = ?, updated_at = ? WHERE id = ?",
                (model, effort, now, session_id)
            )
            conn.commit()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        thinking: str = "",
        tokens: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cost: float = 0.0
    ) -> str:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO messages (
                    id, session_id, role, content, thinking, tokens,
                    input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens,
                    cost, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    msg_id, session_id, role, content, thinking, tokens,
                    input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens,
                    cost, now
                )
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            conn.commit()
        return msg_id

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
            return [dict(row) for row in cur.fetchall()]

    def update_session_title(self, session_id: str, new_title: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (new_title, now, session_id))
            conn.commit()

    def delete_session(self, session_id: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
