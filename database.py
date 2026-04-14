# Save Notes: The Persistence Engine (Phase 2 - SQLite WAL Engine)
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Implemented strict atomic transactions, WAL mode, and singleton metadata table.

import sqlite3
import logging
from pathlib import Path
from typing import Generator, Any, List, Dict, Optional
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "floatslate.db"

class DatabaseManager:
    """Handles thread-safe SQLite operations with strict atomic transaction boundaries."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Provides an atomic transaction boundary. 
        Auto-commits on success, auto-rolls back on Python exceptions.
        """
        # isolation_level=None disables sqlite3's implicit transaction management,
        # allowing us to manually enforce BEGIN/COMMIT for strict atomicity.
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        
        # Enforce WAL mode for concurrent read/write stability and crash resistance
        conn.execute("PRAGMA journal_mode=WAL;")
        # NORMAL synchronous is safe in WAL mode and much faster than FULL
        conn.execute("PRAGMA synchronous=NORMAL;")
        
        cursor = conn.cursor()
        cursor.execute("BEGIN;")
        try:
            yield cursor
            cursor.execute("COMMIT;")
        except Exception as e:
            cursor.execute("ROLLBACK;")
            logging.error(f"Database transaction failed. Rolled back. Reason: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def _init_db(self) -> None:
        """Bootstraps the required tables if they do not exist."""
        with self.transaction() as cur:
            # Table 1: Global App Metadata (Salt, Schema Versions, etc.)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL
                )
            """)
            
            # Table 2: The Vault Payload & Geometrics
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content BLOB, -- Encrypted Payload from security.py
                    theme_index INTEGER NOT NULL DEFAULT 6,
                    pos_x INTEGER NOT NULL DEFAULT 0,
                    pos_y INTEGER NOT NULL DEFAULT 0,
                    width INTEGER NOT NULL DEFAULT 200,
                    height INTEGER NOT NULL DEFAULT 300,
                    is_rolled_up BOOLEAN NOT NULL CHECK (is_rolled_up IN (0, 1)) DEFAULT 0
                )
            """)

    # --- App Metadata Operations ---
    
    def get_meta(self, key: str) -> Optional[bytes]:
        """Retrieves a global metadata BLOB (e.g., the decryption salt)."""
        with self.transaction() as cur:
            cur.execute("SELECT value FROM app_meta WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else None

    def set_meta(self, key: str, value: bytes) -> None:
        """Upserts a global metadata BLOB."""
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO app_meta (key, value) 
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))

    # --- Note CRUD Operations ---

    def upsert_note(self, note_data: Dict[str, Any]) -> int:
        """
        Inserts a new note or updates an existing one. 
        Returns the row ID.
        """
        with self.transaction() as cur:
            if note_data.get("id") is None:
                cur.execute("""
                    INSERT INTO notes (title, content, theme_index, pos_x, pos_y, width, height, is_rolled_up)
                    VALUES (:title, :content, :theme_index, :pos_x, :pos_y, :width, :height, :is_rolled_up)
                """, note_data)
                return cur.lastrowid # type: ignore
            else:
                cur.execute("""
                    UPDATE notes SET
                        title = :title,
                        content = :content,
                        theme_index = :theme_index,
                        pos_x = :pos_x,
                        pos_y = :pos_y,
                        width = :width,
                        height = :height,
                        is_rolled_up = :is_rolled_up
                    WHERE id = :id
                """, note_data)
                return note_data["id"]

    def load_all_notes(self) -> List[Dict[str, Any]]:
        """Retrieves all notes for the boot-phase restoration."""
        with self.transaction() as cur:
            # Using dict mapping to pass clean kwargs directly to UI instances
            cur.execute("SELECT id, title, content, theme_index, pos_x, pos_y, width, height, is_rolled_up FROM notes")
            rows = cur.fetchall()
            
            return [
                {
                    "id": r[0],
                    "title": r[1],
                    "content": r[2],
                    "theme_index": r[3],
                    "pos_x": r[4],
                    "pos_y": r[5],
                    "width": r[6],
                    "height": r[7],
                    "is_rolled_up": bool(r[8])
                }
                for r in rows
            ]

    def delete_note(self, note_id: int) -> None:
        """Permanently purges a note from the database."""
        with self.transaction() as cur:
            cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    def update_all_notes_atomic(self, notes_data: List[Dict[str, Any]]) -> None:
        """
        OWASP/ACID Compliance: Bulk updates all notes in a single WAL transaction.
        If any encryption fails, the entire database rolls back to the previous key state.
        """
        with self.transaction() as cur:
            for note in notes_data:
                cur.execute("""
                    UPDATE notes SET content = :content WHERE id = :id
                """, {"content": note["content"], "id": note["id"]})