"""
Arooj Cloth and Bedsheet Parda - Database Connection & SQLite Manager
Ensures strict ACID guarantees, foreign keys, WAL mode, transactions, and online backups.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union
from app.config import get_db_path

class DatabaseManager:
    """Manages SQLite database connections, transactions, pragmas, and backups."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else get_db_path()
        self._local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a thread-local SQLite connection configured with proper pragmas."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=20.0,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            # Enforce foreign key constraints and fast WAL mode for retail reliability
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA busy_timeout = 5000;")
            cursor.close()
            self._local.conn = conn

        return self._local.conn

    def close(self):
        """Closes the thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions.
        Commits upon normal completion, rolls back on exception.
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def backup_to_file(self, target_path: Union[str, Path]) -> bool:
        """
        Uses SQLite's live online backup API to take a non-blocking, safe snapshot.
        This guarantees complete data integrity without file corruption.
        """
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        source_conn = self.get_connection()
        dest_conn = sqlite3.connect(str(target_path))
        try:
            with dest_conn:
                source_conn.backup(dest_conn, pages=100)
            return True
        finally:
            dest_conn.close()

    def restore_from_file(self, backup_path: Union[str, Path]) -> bool:
        """
        Restores the database from a backup file safely using SQLite backup API.
        Verifies the backup file before completing restore.
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Verify backup integrity first
        test_conn = sqlite3.connect(str(backup_path))
        try:
            c = test_conn.cursor()
            c.execute("PRAGMA integrity_check;")
            res = c.fetchone()
            if not res or res[0] != "ok":
                raise ValueError("Corrupted backup file: integrity check failed")
        finally:
            test_conn.close()

        # Restore into live database
        target_conn = self.get_connection()
        source_conn = sqlite3.connect(str(backup_path))
        try:
            with target_conn:
                source_conn.backup(target_conn, pages=100)
            return True
        finally:
            source_conn.close()

# Global default manager instance
db_manager = DatabaseManager()
