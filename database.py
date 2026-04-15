# Save Notes: The Persistence Engine 
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Injected safe ALTER TABLE migration for created_at timestamps.

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
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
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
        with self.transaction() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content BLOB, 
                    theme_index INTEGER NOT NULL DEFAULT 6,
                    pos_x INTEGER NOT NULL DEFAULT 0,
                    pos_y INTEGER NOT NULL DEFAULT 0,
                    width INTEGER NOT NULL DEFAULT 200,
                    height INTEGER NOT NULL DEFAULT 300,
                    is_rolled_up BOOLEAN NOT NULL CHECK (is_rolled_up IN (0, 1)) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Non-destructive migration for existing databases
            try:
                cur.execute("ALTER TABLE notes ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            except sqlite3.OperationalError:
                pass # Column already exists, proceed normally
                
            # --- Crash Telemetry Table ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crash_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    traceback TEXT
                )
            """)

    def log_crash(self, traceback_str: str) -> None:
        """Safely writes a crash log to the database using the atomic context manager."""
        try:
            with self.transaction() as cur:
                cur.execute("INSERT INTO crash_logs (traceback) VALUES (?)", (traceback_str,))
        except Exception as e:
            # Failsafe: Print to terminal if SQLite is completely locked during a hard crash
            print(f"Failed to write crash to database: {e}")

    def cleanup_old_logs(self, days: int = 30) -> None:
        """Purges crash logs older than the specified number of days."""
        import sqlite3
        try:
            # 1. Perform the deletion within a safe transaction
            with self.transaction() as cur:
                cur.execute(
                    "DELETE FROM crash_logs WHERE timestamp < datetime('now', ?)", 
                    (f'-{days} days',)
                )
            
            # 2. VACUUM must happen OUTSIDE of an active transaction block
            # We open a temporary raw connection just for this optimization
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM;")
            conn.close()
            
        except Exception as e:
            # This ensures background errors never interrupt the user's workflow
            print(f"Background maintenance failed: {e}")
    
    def export_crash_logs(self, file_path: str) -> bool:
        """Exports all telemetry data to a plain text file."""
        with self.transaction() as cur:
            cur.execute("SELECT timestamp, traceback FROM crash_logs ORDER BY id DESC")
            rows = cur.fetchall()
            
            if not rows:
                return False
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=== FLOATIES CRASH TELEMETRY ===\n\n")
                for row in rows:
                    f.write(f"[{row[0]}]\n{row[1]}\n")
                    f.write("-" * 50 + "\n\n")
            return True

    def get_meta(self, key: str) -> Optional[bytes]:
        with self.transaction() as cur:
            cur.execute("SELECT value FROM app_meta WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else None

    def set_meta(self, key: str, value: bytes) -> None:
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO app_meta (key, value) 
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))

    def upsert_note(self, note_data: Dict[str, Any]) -> int:
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
        with self.transaction() as cur:
            cur.execute("SELECT id, title, content, theme_index, pos_x, pos_y, width, height, is_rolled_up, created_at FROM notes")
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
                    "is_rolled_up": bool(r[8]),
                    "created_at": r[9]
                }
                for r in rows
            ]

    def delete_note(self, note_id: int) -> None:
        with self.transaction() as cur:
            cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    def update_all_notes_atomic(self, notes_data: List[Dict[str, Any]]) -> None:
        with self.transaction() as cur:
            for note in notes_data:
                cur.execute("""
                    UPDATE notes SET content = :content WHERE id = :id
                """, {"content": note["content"], "id": note["id"]})