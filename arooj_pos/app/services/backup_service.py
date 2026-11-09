"""
Backup & Restore Service for Arooj POS
Uses SQLite's online backup API for safe, non-blocking zero-corruption snapshots.
Provides:
- Create Local Backup
- Backup to USB / External Drive
- Restore from Backup with safety snapshot
- Automatic daily local backup
"""

import os
import logging
import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import get_app_data_dir
from app.database import DatabaseManager

logger = logging.getLogger("arooj_pos.backup")

class BackupService:
    def __init__(self, db_manager: DatabaseManager, backup_dir: Optional[Path] = None):
        self.db_manager = db_manager
        self.backup_dir = Path(backup_dir) if backup_dir else (get_app_data_dir() / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, custom_target_dir: Optional[Path] = None, prefix: str = "arooj_pos_backup_") -> Path:
        """
        Creates a verified snapshot of the active SQLite database using online backup API.
        """
        target_dir = Path(custom_target_dir) if custom_target_dir else self.backup_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = target_dir / f"{prefix}{timestamp}.db"

        self.db_manager.backup_to_file(backup_file)
        logger.info(f"Database backup created successfully: {backup_file}")
        return backup_file

    def check_and_run_daily_backup(self) -> Optional[Path]:
        """
        Automatically performs a daily local backup on application startup if none was created today.
        Returns the newly created Path, or None if a daily backup already exists for today.
        """
        today_prefix = datetime.datetime.now().strftime("%Y%m%d")
        existing_today = list(self.backup_dir.glob(f"arooj_pos_daily_{today_prefix}*.db"))
        if existing_today:
            logger.info(f"Daily backup already exists for today ({len(existing_today)} found). Skipping auto-backup.")
            return None

        try:
            logger.info("Executing scheduled automatic daily local backup...")
            backup_file = self.create_backup(prefix="arooj_pos_daily_")
            return backup_file
        except Exception as e:
            logger.error(f"Failed to create automatic daily backup: {e}")
            return None

    def list_backups(self) -> List[dict]:
        """Lists existing backups with file size and creation time."""
        backups = []
        for f in self.backup_dir.glob("*.db"):
            try:
                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception:
                pass
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def get_last_backup_info(self) -> Optional[dict]:
        """Returns the most recent backup metadata, or None."""
        backups = self.list_backups()
        return backups[0] if backups else None

    def restore_backup(self, backup_file_path: Path) -> bool:
        """
        Restores database from a selected backup.
        Takes a safety snapshot before replacing live database to protect against data loss.
        """
        backup_file_path = Path(backup_file_path)
        if not backup_file_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")

        # 1. Safety snapshot of current database
        try:
            safety_file = self.create_backup(prefix="arooj_pos_safety_pre_restore_")
            logger.info(f"Pre-restore safety snapshot stored at: {safety_file}")
        except Exception as e:
            logger.warning(f"Could not create pre-restore snapshot: {e}")

        # 2. Restore from designated backup
        success = self.db_manager.restore_from_file(backup_file_path)
        logger.info(f"Database restore from {backup_file_path.name} finished with status: {success}")
        return success
