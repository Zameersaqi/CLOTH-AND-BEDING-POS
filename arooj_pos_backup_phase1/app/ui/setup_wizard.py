"""
First-Run Setup Wizard for Arooj Cloth and Bedsheet Parda
Guides non-technical retail owner through initial store profile, printer size, and admin credentials.
"""

from typing import Optional
from app.repositories.settings_repository import SettingsRepository
from app.repositories.user_repository import UserRepository

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QComboBox, QFormLayout, QMessageBox
    )
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QDialog = object

if PYSIDE_AVAILABLE:
    class SetupWizardDialog(QDialog):
        def __init__(self, settings_repo: SettingsRepository, user_repo: UserRepository, parent=None):
            super().__init__(parent)
            self.settings_repo = settings_repo
            self.user_repo = user_repo
            self.setWindowTitle("Arooj POS - First Run Store Setup (پہلی بار سیٹ اپ)")
            self.setMinimumWidth(440)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(14)

            title = QLabel("Welcome to Arooj POS Software!\nخوش آمدید! دکان کی بنیادی معلومات درج فرمائیں")
            title.setStyleSheet("font-size: 15px; font-weight: bold; color: #064e3b; text-align: center;")
            layout.addWidget(title)

            form = QFormLayout()

            self.shop_name = QLineEdit("Arooj Cloth and Bedsheet Parda")
            form.addRow("Shop Name:", self.shop_name)

            self.shop_phone = QLineEdit("+92 300 1234567")
            form.addRow("Contact Phone:", self.shop_phone)

            self.shop_address = QLineEdit("Main Bazaar, Commercial Center, Pakistan")
            form.addRow("Shop Address:", self.shop_address)

            self.paper_width = QComboBox()
            self.paper_width.addItems(["80mm (Standard)", "58mm (Compact)"])
            form.addRow("Thermal Printer Size:", self.paper_width)

            self.admin_pwd = QLineEdit("admin")
            self.admin_pwd.setEchoMode(QLineEdit.Password)
            form.addRow("Admin Password:", self.admin_pwd)

            self.mgr_pin = QLineEdit("1234")
            form.addRow("Manager PIN (Price Changes):", self.mgr_pin)

            layout.addLayout(form)

            note = QLabel("Note: Preloaded Pakistani clothing and bedding catalog has been automatically created. You can enter real stock quantities and negotiated prices anytime.")
            note.setWordWrap(True)
            note.setStyleSheet("font-size: 11px; color: #64748b; background: #f1f5f9; padding: 8px; border-radius: 4px;")
            layout.addWidget(note)

            btn_box = QHBoxLayout()
            start_btn = QPushButton("Start POS Billing (شروع کریں)")
            start_btn.setStyleSheet("background-color: #059669; color: white; font-weight: 800; font-size: 14px; padding: 10px;")
            start_btn.clicked.connect(self.on_save)
            btn_box.addWidget(start_btn)
            layout.addLayout(btn_box)

        def on_save(self):
            name = self.shop_name.text().strip()
            phone = self.shop_phone.text().strip()
            addr = self.shop_address.text().strip()
            pw = "80mm" if "80mm" in self.paper_width.currentText() else "58mm"
            pin = self.mgr_pin.text().strip() or "1234"

            self.settings_repo.set_setting("shop_name", name)
            self.settings_repo.set_setting("shop_phone", phone)
            self.settings_repo.set_setting("shop_address", addr)
            self.settings_repo.set_setting("receipt_paper_width", pw)
            self.settings_repo.set_setting("manager_pin", pin)
            self.settings_repo.set_setting("first_run_completed", "1")

            self.accept()
else:
    class SetupWizardDialog:
        pass
