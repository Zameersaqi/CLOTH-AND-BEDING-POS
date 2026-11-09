"""
Login Dialog for Arooj Cloth and Bedsheet Parda
Authenticates staff/manager/admin accounts and prevents unauthorized access.
"""

from typing import Optional
from app.models.entities import User
from app.repositories.user_repository import UserRepository

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QFormLayout, QMessageBox, QFrame
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QDialog = object

if PYSIDE_AVAILABLE:
    class LoginDialog(QDialog):
        def __init__(self, user_repo: UserRepository, shop_name: str = "Arooj Cloth and Bedsheet Parda", parent=None):
            super().__init__(parent)
            self.user_repo = user_repo
            self.shop_name = shop_name
            self.authenticated_user: Optional[User] = None

            self.setWindowTitle(f"Login - {shop_name}")
            self.setFixedSize(380, 320)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(14)

            # Header
            header_box = QVBoxLayout()
            title = QLabel(self.shop_name)
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #064e3b; text-align: center;")
            title.setAlignment(Qt.AlignCenter)

            subtitle = QLabel("Staff Login (لاگ ان)")
            subtitle.setStyleSheet("font-size: 13px; color: #047857; font-weight: 600;")
            subtitle.setAlignment(Qt.AlignCenter)

            header_box.addWidget(title)
            header_box.addWidget(subtitle)
            layout.addLayout(header_box)

            # Form
            form = QFormLayout()
            self.username_input = QLineEdit()
            self.username_input.setPlaceholderText("Enter username (e.g. admin)...")
            self.username_input.setText("admin")  # Convenience default for quick field focus
            form.addRow("Username:", self.username_input)

            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.setPlaceholderText("Enter password...")
            self.password_input.returnPressed.connect(self.on_login)
            form.addRow("Password:", self.password_input)

            layout.addLayout(form)

            # Error Label
            self.error_label = QLabel("")
            self.error_label.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: bold;")
            self.error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.error_label)

            # Buttons
            btn_box = QHBoxLayout()
            login_btn = QPushButton("Login to POS (لاگ ان)")
            login_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px; font-size: 13px;")
            login_btn.clicked.connect(self.on_login)

            cancel_btn = QPushButton("Exit (بند کریں)")
            cancel_btn.clicked.connect(self.reject)

            btn_box.addWidget(cancel_btn)
            btn_box.addWidget(login_btn, stretch=2)
            layout.addLayout(btn_box)

        def on_login(self):
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()

            if not username or not password:
                self.error_label.setText("Please enter both username and password.")
                return

            user = self.user_repo.authenticate(username, password)
            if user:
                self.authenticated_user = user
                self.accept()
            else:
                self.error_label.setText("Incorrect username or password. Please try again.")
                self.password_input.clear()
                self.password_input.setFocus()
else:
    class LoginDialog:
        pass
