"""
Settings & Business Configuration Screen for Arooj POS
Manages shop profile, Urdu branding, logo upload, thermal printer width, manager PIN,
password change workflow, and safe USB/local database backups.
"""

from pathlib import Path
import shutil
from typing import Optional
from app.config import get_app_data_dir
from app.ui.backup_dialog import BackupDialog

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QComboBox, QFormLayout, QFileDialog, QMessageBox, QGroupBox, QScrollArea
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap, QImage
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class SettingsScreen(QWidget):
        def __init__(self, settings_repo, backup_service, user_repo=None, current_user=None, parent=None):
            super().__init__(parent)
            self.settings_repo = settings_repo
            self.backup_service = backup_service
            self.user_repo = user_repo
            self.current_user = current_user
            self.logo_path = ""
            self.init_ui()
            self.load_settings()

        def init_ui(self):
            outer_layout = QVBoxLayout(self)
            outer_layout.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content_widget = QWidget()
            layout = QVBoxLayout(content_widget)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)

            title = QLabel("Shop Profile & System Settings (دکان کی ترتیبات)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            layout.addWidget(title)

            # 1. Profile Group
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

            # 2. Printer & Policy Group
            print_group = QGroupBox("Thermal Printer & Receipt Customization")
            form2 = QFormLayout(print_group)

            self.paper_width_combo = QComboBox()
            self.paper_width_combo.addItems(["80mm", "58mm"])
            form2.addRow("Receipt Paper Width:", self.paper_width_combo)

            from app.services.printer_service import PrinterService
            self.test_printer_service = PrinterService()
            self.printer_combo = QComboBox()
            available_printers = self.test_printer_service.get_available_printers()
            self.printer_combo.addItems(available_printers)
            form2.addRow("Windows Thermal Printer:", self.printer_combo)

            test_print_btn = QPushButton("🖨️ Print Test Receipt (ٹیسٹ پرنٹ رسید)")
            test_print_btn.setStyleSheet("background-color: #0d9488; color: white; font-weight: bold; padding: 6px 14px;")
            test_print_btn.clicked.connect(self.on_print_test_receipt)
            form2.addRow("Printer Verification:", test_print_btn)

            self.footer_input = QLineEdit()
            form2.addRow("Receipt Footer / Return Policy:", self.footer_input)

            self.pin_input = QLineEdit()
            self.pin_input.setEchoMode(QLineEdit.Password)
            form2.addRow("Manager PIN (Price Overrides):", self.pin_input)

            layout.addWidget(print_group)

            # 3. Security & Password Change Group
            sec_group = QGroupBox("Staff Security & Password Change")
            form_sec = QFormLayout(sec_group)

            user_title = f"{self.current_user.full_name} ({self.current_user.username})" if self.current_user else "Current Staff"
            role_title = self.current_user.role.upper() if self.current_user else "ADMIN"
            form_sec.addRow("Logged In User:", QLabel(f"<b>{user_title}</b>  [Role: {role_title}]"))

            self.curr_pwd_input = QLineEdit()
            self.curr_pwd_input.setEchoMode(QLineEdit.Password)
            self.curr_pwd_input.setPlaceholderText("Enter existing password...")
            form_sec.addRow("Current Password:", self.curr_pwd_input)

            self.new_pwd_input = QLineEdit()
            self.new_pwd_input.setEchoMode(QLineEdit.Password)
            self.new_pwd_input.setPlaceholderText("Enter new password...")
            form_sec.addRow("New Password:", self.new_pwd_input)

            self.confirm_new_pwd = QLineEdit()
            self.confirm_new_pwd.setEchoMode(QLineEdit.Password)
            self.confirm_new_pwd.setPlaceholderText("Confirm new password...")
            form_sec.addRow("Confirm New Password:", self.confirm_new_pwd)

            change_pwd_btn = QPushButton("Update Password Now")
            change_pwd_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px;")
            change_pwd_btn.clicked.connect(self.on_change_password)
            form_sec.addRow("", change_pwd_btn)

            layout.addWidget(sec_group)

            # 4. Logo & Backup Group
            data_group = QGroupBox("Branding Logo & Database Backups (ڈیٹا کی حفاظت)")
            form3 = QFormLayout(data_group)

            # Shop Logo Branding with preview thumbnail
            logo_container = QHBoxLayout()
            logo_container.setSpacing(12)

            self.logo_preview_lbl = QLabel("No Logo")
            self.logo_preview_lbl.setFixedSize(120, 80)
            self.logo_preview_lbl.setAlignment(Qt.AlignCenter)
            self.logo_preview_lbl.setStyleSheet("border: 2px dashed #cbd5e1; border-radius: 6px; background-color: #f8fafc; color: #94a3b8; font-weight: bold;")
            logo_container.addWidget(self.logo_preview_lbl)

            logo_btn_box = QVBoxLayout()
            logo_btn_box.setSpacing(6)

            self.browse_logo_btn = QPushButton("📁 Browse Logo...")
            self.browse_logo_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px;")
            self.browse_logo_btn.clicked.connect(self.on_browse_logo)

            self.remove_logo_btn = QPushButton("🗑️ Remove Logo")
            self.remove_logo_btn.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 6px 14px;")
            self.remove_logo_btn.clicked.connect(self.on_remove_logo)
            self.remove_logo_btn.setVisible(False)

            self.logo_info_lbl = QLabel("Accepted: PNG, JPG, JPEG, BMP (Scaled for 80mm/58mm thermal receipts)")
            self.logo_info_lbl.setStyleSheet("color: #64748b; font-size: 11px;")

            btn_row = QHBoxLayout()
            btn_row.addWidget(self.browse_logo_btn)
            btn_row.addWidget(self.remove_logo_btn)
            btn_row.addStretch()

            logo_btn_box.addLayout(btn_row)
            logo_btn_box.addWidget(self.logo_info_lbl)
            logo_container.addLayout(logo_btn_box, stretch=1)

            form3.addRow("Shop Logo Branding:", logo_container)

            backup_box = QHBoxLayout()
            mgr_btn = QPushButton("🗄️ Full Backup Manager (مکمل بیک اپ مینیجر)")
            mgr_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 14px;")
            mgr_btn.clicked.connect(self.on_open_backup_manager)

            backup_btn = QPushButton("Create Local Backup")
            backup_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px;")
            backup_btn.clicked.connect(self.on_create_backup)

            usb_backup_btn = QPushButton("Backup to USB / External")
            usb_backup_btn.setStyleSheet("background-color: #0d9488; color: white; font-weight: bold; padding: 6px 14px;")
            usb_backup_btn.clicked.connect(self.on_usb_backup)

            restore_btn = QPushButton("Restore From Backup")
            restore_btn.setStyleSheet("background-color: #d97706; color: white; font-weight: bold; padding: 6px 14px;")
            restore_btn.clicked.connect(self.on_restore_backup)

            backup_box.addWidget(mgr_btn)
            backup_box.addWidget(backup_btn)
            backup_box.addWidget(usb_backup_btn)
            backup_box.addWidget(restore_btn)
            backup_box.addStretch()
            form3.addRow("Data Safety Actions:", backup_box)

            layout.addWidget(data_group)

            # Save Button
            save_btn = QPushButton("Save Settings (ترتیبات محفوظ کریں)")
            save_btn.setStyleSheet("background-color: #059669; color: white; font-size: 15px; font-weight: bold; padding: 12px 24px;")
            save_btn.clicked.connect(self.on_save)
            layout.addWidget(save_btn)
            layout.addStretch()

            scroll.setWidget(content_widget)
            outer_layout.addWidget(scroll)

        def load_settings(self):
            s = self.settings_repo.get_all_settings()
            self.name_input.setText(s.get("shop_name", "Arooj Cloth and Bedsheet Parda"))
            self.urdu_name_input.setText(s.get("shop_name_urdu", "عروج کلوتھ اینڈ بیڈ شیٹ پردہ"))
            self.phone_input.setText(s.get("shop_phone", "0300-0000000"))
            self.address_input.setText(s.get("shop_address", "Main Commercial Market, Pakistan"))
            self.paper_width_combo.setCurrentText(s.get("receipt_paper_width", "80mm"))
            def_printer = s.get("default_printer", "")
            if def_printer and self.printer_combo.findText(def_printer) != -1:
                self.printer_combo.setCurrentText(def_printer)
            self.footer_input.setText(s.get("receipt_footer_text", "Exchange possible within 7 days with original receipt."))
            self.pin_input.setText(s.get("manager_pin", "1234"))

            self.logo_path = s.get("shop_logo_path", "")
            self.update_logo_preview()

        def update_logo_preview(self):
            """Renders scaled thumbnail or placeholder and toggles remove button."""
            if self.logo_path and Path(self.logo_path).exists():
                pix = QPixmap(self.logo_path)
                if not pix.isNull():
                    scaled = pix.scaled(116, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_preview_lbl.setPixmap(scaled)
                    self.logo_preview_lbl.setStyleSheet("border: 1px solid #10b981; border-radius: 6px; background-color: #f0fdf4;")
                    self.browse_logo_btn.setText("🔄 Change Logo...")
                    self.remove_logo_btn.setVisible(True)
                    self.logo_info_lbl.setText(f"Active Logo: {Path(self.logo_path).name}")
                    return

            self.logo_preview_lbl.clear()
            self.logo_preview_lbl.setText("No Logo")
            self.logo_preview_lbl.setStyleSheet("border: 2px dashed #cbd5e1; border-radius: 6px; background-color: #f8fafc; color: #94a3b8; font-weight: bold;")
            self.browse_logo_btn.setText("📁 Browse Logo...")
            self.remove_logo_btn.setVisible(False)
            self.logo_info_lbl.setText("Accepted: PNG, JPG, JPEG, BMP (Scaled for 80mm/58mm thermal receipts)")

        def on_print_test_receipt(self):
            current_settings = {
                "shop_name": self.name_input.text().strip() or "Arooj Cloth and Bedsheet Parda",
                "shop_name_urdu": self.urdu_name_input.text().strip(),
                "shop_phone": self.phone_input.text().strip(),
                "shop_address": self.address_input.text().strip(),
                "receipt_paper_width": self.paper_width_combo.currentText(),
                "receipt_footer_text": self.footer_input.text().strip(),
                "shop_logo_path": self.logo_path
            }
            from app.services.printer_service import PrinterService
            printer_service = PrinterService(paper_width=self.paper_width_combo.currentText())
            selected_printer = self.printer_combo.currentText()
            success, msg = printer_service.print_test_receipt(current_settings, printer_name=selected_printer)
            if success:
                QMessageBox.information(self, "Test Print Success", msg)
            else:
                QMessageBox.critical(self, "Test Print Failed", f"{msg}\n\nPlease check thermal printer connection and paper roll.")

        def on_browse_logo(self):
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Shop Logo Image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)"
            )
            if not file_path:
                return

            # Validate corrupt or invalid image
            test_img = QImage(file_path)
            if test_img.isNull():
                QMessageBox.critical(self, "Invalid Image", "The selected file is not a valid or readable image.\nPlease select a valid PNG, JPG, JPEG, or BMP file.")
                return

            dest_dir = get_app_data_dir() / "logos"
            dest_dir.mkdir(parents=True, exist_ok=True)
            import uuid
            ext = Path(file_path).suffix.lower() or ".png"
            dest_path = dest_dir / f"logo_{uuid.uuid4().hex[:8]}{ext}"
            try:
                shutil.copy2(file_path, dest_path)
                self.logo_path = str(dest_path)
                self.settings_repo.set_setting("shop_logo_path", self.logo_path)
                self.update_logo_preview()
                QMessageBox.information(self, "Logo Updated", f"Store logo successfully saved and active!\nFile: {dest_path.name}")
            except Exception as e:
                QMessageBox.critical(self, "Logo Save Failed", f"Failed to save logo file: {e}")

        def on_remove_logo(self):
            reply = QMessageBox.question(
                self, "Confirm Remove Logo", "Are you sure you want to remove the shop logo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.logo_path = ""
                self.settings_repo.set_setting("shop_logo_path", "")
                self.update_logo_preview()

        def on_change_password(self):
            if not self.user_repo or not self.current_user:
                QMessageBox.warning(self, "Notice", "User authentication service is not available.")
                return

            curr = self.curr_pwd_input.text().strip()
            new_p = self.new_pwd_input.text().strip()
            conf = self.confirm_new_pwd.text().strip()

            if not curr or not new_p:
                QMessageBox.warning(self, "Required Fields", "Please enter your current and new password.")
                return

            if new_p != conf:
                QMessageBox.warning(self, "Mismatch", "New password and confirmation do not match.")
                return

            if len(new_p) < 4:
                QMessageBox.warning(self, "Weak Password", "New password must be at least 4 characters long.")
                return

            success, msg = self.user_repo.update_password(self.current_user.id, curr, new_p)
            if success:
                QMessageBox.information(self, "Password Changed", "Your password has been updated successfully!")
                self.curr_pwd_input.clear()
                self.new_pwd_input.clear()
                self.confirm_new_pwd.clear()
            else:
                QMessageBox.critical(self, "Password Change Failed", msg)

        def on_save(self):
            self.settings_repo.set_setting("shop_name", self.name_input.text().strip())
            self.settings_repo.set_setting("shop_name_urdu", self.urdu_name_input.text().strip())
            self.settings_repo.set_setting("shop_phone", self.phone_input.text().strip())
            self.settings_repo.set_setting("shop_address", self.address_input.text().strip())
            self.settings_repo.set_setting("receipt_paper_width", self.paper_width_combo.currentText())
            self.settings_repo.set_setting("default_printer", self.printer_combo.currentText())
            self.settings_repo.set_setting("receipt_footer_text", self.footer_input.text().strip())
            self.settings_repo.set_setting("manager_pin", self.pin_input.text().strip())
            if self.logo_path:
                self.settings_repo.set_setting("shop_logo_path", self.logo_path)

            QMessageBox.information(self, "Settings Saved", "All shop profile, receipt settings, printer and PIN updated successfully!")

        def on_open_backup_manager(self):
            if not self.backup_service:
                QMessageBox.warning(self, "Backup Unavailable", "Backup service is not initialized.")
                return
            dlg = BackupDialog(backup_service=self.backup_service, parent=self)
            dlg.exec()

        def on_create_backup(self):
            try:
                dest = self.backup_service.create_backup()
                QMessageBox.information(self, "Backup Success", f"Database safely backed up to:\n{dest.name}\nLocation: {dest.parent}")
            except Exception as e:
                QMessageBox.critical(self, "Backup Error", str(e))

        def on_usb_backup(self):
            usb_dir = QFileDialog.getExistingDirectory(self, "Select USB Drive or External Backup Folder")
            if usb_dir:
                try:
                    dest = self.backup_service.create_backup(Path(usb_dir))
                    QMessageBox.information(self, "USB Backup Complete", f"Backup snapshot created on USB drive:\n{dest}")
                except Exception as e:
                    QMessageBox.critical(self, "USB Backup Failed", str(e))

        def on_restore_backup(self):
            file_path, _ = QFileDialog.getOpenFileName(self, "Select SQLite Backup File to Restore", str(self.backup_service.backup_dir), "SQLite Database (*.db)")
            if not file_path:
                return
            reply = QMessageBox.warning(
                self, "Confirm Restore",
                "Restoring will overwrite current transactions with the backup!\nA safety snapshot of current data will be created first.\nProceed?",
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
        def __init__(self, settings_repo=None, backup_service=None, user_repo=None, current_user=None, parent=None, *args, **kwargs):
            self.settings_repo = settings_repo
            self.backup_service = backup_service
            self.user_repo = user_repo
            self.current_user = current_user
