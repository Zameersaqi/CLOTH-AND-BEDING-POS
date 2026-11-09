"""
Backup & Restore Service for Arooj POS
Uses SQLite's online backup API for safe, non-blocking zero-corruption snapshots.
"""

import os
import datetime
from pathlib import Path
from typing import List, Optional
from app.config import get_app_data_dir
from app.database import DatabaseManager

class BackupService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.backup_dir = get_app_data_dir() / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, custom_target_dir: Optional[Path] = None) -> Path:
        """
        Creates a verified snapshot of the active SQLite database using online backup API.
        """
        target_dir = Path(custom_target_dir) if custom_target_dir else self.backup_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = target_dir / f"arooj_pos_backup_{timestamp}.db"

        self.db_manager.backup_to_file(backup_file)
        return backup_file

    def list_backups(self) -> List[dict]:
        """Lists existing backups with file size and creation time."""
        backups = []
        for f in self.backup_dir.glob("*.db"):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "path": str(f),
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def restore_backup(self, backup_file_path: Path) -> bool:
        """
        Restores database from a selected backup.
        Takes a safety snapshot before replacing live database.
        """
        backup_file_path = Path(backup_file_path)
        if not backup_file_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")

        # Safety snapshot
        self.create_backup()

        # Restore
        return self.db_manager.restore_from_file(backup_file_path)
