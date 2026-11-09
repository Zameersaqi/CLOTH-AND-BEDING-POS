"""
Database Backup & Restore Manager Dialog for Arooj POS
Provides:
- Create Local Backup
- Backup to USB / External Drive
- Restore from Backup with safety snapshot
- Automatic daily local backup status
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
        QFileDialog, QFrame, QGroupBox
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QDialog = object

if PYSIDE_AVAILABLE:
    class BackupDialog(QDialog):
        def __init__(self, backup_service, parent=None):
            super().__init__(parent)
            self.backup_service = backup_service
            self.setWindowTitle("Database Backup & Safety Manager (ڈیٹا کی حفاظت و بیک اپ)")
            self.resize(720, 520)
            self.init_ui()
            self.load_backups()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Top Header Info Box
            header_frame = QFrame()
            header_frame.setObjectName("summaryBox")
            h_layout = QVBoxLayout(header_frame)
            h_layout.setContentsMargins(12, 10, 12, 10)

            title_lbl = QLabel("🛡️ SQLite Zero-Loss Database Backup System")
            title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #064e3b;")
            h_layout.addWidget(title_lbl)

            self.status_lbl = QLabel("● Automatic Daily Backup: Active (Protected on every launch)")
            self.status_lbl.setStyleSheet("color: #059669; font-weight: bold; font-size: 12px;")
            h_layout.addWidget(self.status_lbl)

            self.last_backup_lbl = QLabel("Last Backup: Checking...")
            self.last_backup_lbl.setStyleSheet("color: #475569; font-size: 12px;")
            h_layout.addWidget(self.last_backup_lbl)

            layout.addWidget(header_frame)

            # Primary Action Buttons
            btn_box = QHBoxLayout()
            btn_box.setSpacing(10)

            local_btn = QPushButton("💾 Create Local Backup Now")
            local_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 16px;")
            local_btn.clicked.connect(self.on_create_local_backup)

            usb_btn = QPushButton("🔌 Backup to USB / External Drive")
            usb_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px 16px;")
            usb_btn.clicked.connect(self.on_usb_backup)

            restore_file_btn = QPushButton("🔄 Restore from Backup File")
            restore_file_btn.setStyleSheet("background-color: #d97706; color: white; font-weight: bold; padding: 10px 16px;")
            restore_file_btn.clicked.connect(self.on_restore_file)

            btn_box.addWidget(local_btn)
            btn_box.addWidget(usb_btn)
            btn_box.addWidget(restore_file_btn)
            layout.addLayout(btn_box)

            # Backups History Group
            group = QGroupBox("Available Local Backups History")
            g_layout = QVBoxLayout(group)

            self.table = QTableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Date & Time", "Backup Filename", "Size (KB)", "Action"])
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            g_layout.addWidget(self.table)

            layout.addWidget(group)

            # Bottom Close Button
            bot_box = QHBoxLayout()
            bot_box.addStretch()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            bot_box.addWidget(close_btn)
            layout.addLayout(bot_box)

        def load_backups(self):
            backups = self.backup_service.list_backups()
            self.table.setRowCount(len(backups))

            if backups:
                latest = backups[0]
                self.last_backup_lbl.setText(f"Last Local Backup: {latest['created_at']} ({latest['filename']} - {latest['size_kb']} KB)")
            else:
                self.last_backup_lbl.setText("No backups found yet. Click 'Create Local Backup Now' above.")

            for i, b in enumerate(backups):
                date_item = QTableWidgetItem(b["created_at"])
                date_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table.setItem(i, 0, date_item)

                name_item = QTableWidgetItem(b["filename"])
                self.table.setItem(i, 1, name_item)

                size_item = QTableWidgetItem(f"{b['size_kb']} KB")
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 2, size_item)

                # Restore button for this specific backup file
                rest_btn = QPushButton("Restore")
                rest_btn.setStyleSheet("background-color: #f59e0b; color: #1e1e1e; font-weight: bold; padding: 3px 8px;")
                rest_btn.clicked.connect(lambda _, p=b["path"]: self.confirm_and_restore(p))
                self.table.setCellWidget(i, 3, rest_btn)

        def on_create_local_backup(self):
            try:
                dest = self.backup_service.create_backup()
                QMessageBox.information(
                    self,
                    "Backup Created Successfully",
                    f"Local database snapshot saved successfully!\n\nFile: {dest.name}\nDirectory: {dest.parent}"
                )
                self.load_backups()
            except Exception as e:
                QMessageBox.critical(self, "Backup Error", f"Failed to create database backup:\n{str(e)}")

        def on_usb_backup(self):
            usb_dir = QFileDialog.getExistingDirectory(self, "Select USB Drive or External Storage Folder")
            if usb_dir:
                try:
                    dest = self.backup_service.create_backup(Path(usb_dir))
                    QMessageBox.information(
                        self,
                        "USB Backup Successful",
                        f"A verified database backup has been copied to your external drive:\n\n{dest}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "USB Backup Error", f"Failed to backup to selected path:\n{str(e)}")

        def on_restore_file(self):
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select SQLite Backup File to Restore",
                str(self.backup_service.backup_dir),
                "SQLite Database (*.db)"
            )
            if file_path:
                self.confirm_and_restore(file_path)

        def confirm_and_restore(self, file_path_str: str):
            p = Path(file_path_str)
            reply = QMessageBox.warning(
                self,
                "Confirm Database Restore",
                f"Are you sure you want to restore the database from:\n{p.name}?\n\n"
                "WARNING: Current transaction records will be replaced with this snapshot.\n"
                "A safety backup of your current database will be saved automatically before restoring.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    success = self.backup_service.restore_backup(p)
                    if success:
                        QMessageBox.information(
                            self,
                            "Database Restored",
                            f"Database was successfully restored from {p.name}!\n\n"
                            "Please restart the application to refresh all active windows."
                        )
                        self.load_backups()
                    else:
                        QMessageBox.critical(self, "Restore Failed", "Could not restore the selected database.")
                except Exception as e:
                    QMessageBox.critical(self, "Restore Error", f"Restore error:\n{str(e)}")
else:
    class BackupDialog:
        def __init__(self, backup_service, parent=None):
            self.backup_service = backup_service

        def exec(self):
            return 1
