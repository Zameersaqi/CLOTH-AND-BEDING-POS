"""
Settings & Business Configuration Screen for Arooj POS
Manages shop profile, Urdu branding, logo upload, thermal printer width, manager PIN, and backups.
"""

from pathlib import Path
import shutil
from app.config import get_app_data_dir

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QComboBox, QFormLayout, QFileDialog, QMessageBox, QGroupBox
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class SettingsScreen(QWidget):
        def __init__(self, settings_repo, backup_service, parent=None):
            super().__init__(parent)
            self.settings_repo = settings_repo
            self.backup_service = backup_service
            self.logo_path = ""
            self.init_ui()
            self.load_settings()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)

            title = QLabel("Shop Profile & System Settings (دکان کی ترتیبات)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            layout.addWidget(title)

            # Profile Group
            profile_group = QGroupBox("Business Profile & Contact Information")
            form1 = QFormLayout(profile_group)

            self.name_input = QLineEdit()
            form1.addRow("Shop Name (English):", self.name_input)

            self.urdu_name_input = QLineEdit()
            form1.addRow("Shop Name (Urdu):", self.urdu_name_input)

            self.phone_input = QLineEdit()
            form1.addRow("Phone / WhatsApp:", self.phone_input)

            self.address_input = QLineEdit()
            form1.addRow("Shop Address:", self.address_input)

            layout.addWidget(profile_group)

            # Printer & Policy Group
            print_group = QGroupBox("Thermal Printer & Receipt Customization")
            form2 = QFormLayout(print_group)

            self.paper_width_combo = QComboBox()
            self.paper_width_combo.addItems(["80mm", "58mm"])
            form2.addRow("Receipt Paper Width:", self.paper_width_combo)

            self.footer_input = QLineEdit()
            form2.addRow("Receipt Footer / Return Policy:", self.footer_input)

            self.pin_input = QLineEdit()
            self.pin_input.setEchoMode(QLineEdit.Password)
            form2.addRow("Manager PIN (Price Overrides):", self.pin_input)

            layout.addWidget(print_group)

            # Logo & Backup Group
            data_group = QGroupBox("Branding Logo & Database Backups")
            form3 = QFormLayout(data_group)

            logo_box = QHBoxLayout()
            self.logo_label = QLabel("No custom logo selected")
            self.logo_label.setStyleSheet("color: #64748b;")
            browse_logo_btn = QPushButton("Browse Image...")
            browse_logo_btn.clicked.connect(self.on_browse_logo)
            logo_box.addWidget(self.logo_label)
            logo_box.addWidget(browse_logo_btn)
            form3.addRow("Shop Logo File:", logo_box)

            backup_box = QHBoxLayout()
            backup_btn = QPushButton("Create Database Backup Now (بیک اپ بنائیں)")
            backup_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px;")
            backup_btn.clicked.connect(self.on_create_backup)
            restore_btn = QPushButton("Restore From Backup (ریسٹور کریں)")
            restore_btn.setStyleSheet("background-color: #d97706; color: white; font-weight: bold; padding: 6px 14px;")
            restore_btn.clicked.connect(self.on_restore_backup)
            backup_box.addWidget(backup_btn)
            backup_box.addWidget(restore_btn)
            backup_box.addStretch()
            form3.addRow("Data Safety:", backup_box)

            layout.addWidget(data_group)

            # Save Button
            save_btn = QPushButton("Save Settings (ترتیبات محفوظ کریں)")
            save_btn.setStyleSheet("background-color: #059669; color: white; font-size: 15px; font-weight: bold; padding: 12px 24px;")
            save_btn.clicked.connect(self.on_save)
            layout.addWidget(save_btn)
            layout.addStretch()

        def load_settings(self):
            s = self.settings_repo.get_all_settings()
            self.name_input.setText(s.get("shop_name", "Arooj Cloth and Bedsheet Parda"))
            self.urdu_name_input.setText(s.get("shop_name_urdu", "عروج کلوتھ اینڈ بیڈ شیٹ پردہ"))
            self.phone_input.setText(s.get("shop_phone", "0300-0000000"))
            self.address_input.setText(s.get("shop_address", "Main Commercial Market, Pakistan"))
            self.paper_width_combo.setCurrentText(s.get("receipt_paper_width", "80mm"))
            self.footer_input.setText(s.get("receipt_footer_text", "Exchange possible within 7 days with original receipt."))
            self.pin_input.setText(s.get("manager_pin", "1234"))

            self.logo_path = s.get("shop_logo_path", "")
            if self.logo_path and Path(self.logo_path).exists():
                self.logo_label.setText(f"Active: {Path(self.logo_path).name}")

        def on_browse_logo(self):
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Shop Logo Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
            if file_path:
                dest_dir = get_app_data_dir() / "logos"
                dest_path = dest_dir / f"logo_{Path(file_path).name}"
                shutil.copy2(file_path, dest_path)
                self.logo_path = str(dest_path)
                self.logo_label.setText(f"Selected: {dest_path.name}")

        def on_save(self):
            self.settings_repo.set_setting("shop_name", self.name_input.text().strip())
            self.settings_repo.set_setting("shop_name_urdu", self.urdu_name_input.text().strip())
            self.settings_repo.set_setting("shop_phone", self.phone_input.text().strip())
            self.settings_repo.set_setting("shop_address", self.address_input.text().strip())
            self.settings_repo.set_setting("receipt_paper_width", self.paper_width_combo.currentText())
            self.settings_repo.set_setting("receipt_footer_text", self.footer_input.text().strip())
            self.settings_repo.set_setting("manager_pin", self.pin_input.text().strip())
            if self.logo_path:
                self.settings_repo.set_setting("shop_logo_path", self.logo_path)

            QMessageBox.information(self, "Settings Saved", "All shop profile and thermal printer settings saved successfully!")

        def on_create_backup(self):
            try:
                dest = self.backup_service.create_backup()
                QMessageBox.information(self, "Backup Success", f"Database safely backed up to:\n{dest.name}\nLocation: {dest.parent}")
            except Exception as e:
                QMessageBox.critical(self, "Backup Error", str(e))

        def on_restore_backup(self):
            file_path, _ = QFileDialog.getOpenFileName(self, "Select SQLite Backup File to Restore", str(self.backup_service.backup_dir), "SQLite Database (*.db)")
            if not file_path:
                return
            reply = QMessageBox.warning(
                self, "Confirm Restore",
                "Restoring will overwrite current transactions with the backup!\nA safety snapshot will be created automatically.\nProceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    self.backup_service.restore_backup(Path(file_path))
                    QMessageBox.information(self, "Restore Completed", "Database restored successfully from backup!")
                except Exception as e:
                    QMessageBox.critical(self, "Restore Error", str(e))
else:
    class SettingsScreen:
        pass
