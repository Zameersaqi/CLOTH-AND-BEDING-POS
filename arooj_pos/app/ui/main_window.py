"""
Main Application Window for Arooj Cloth and Bedsheet Parda Desktop POS
"""

import sys
from pathlib import Path
from app.config import APP_NAME, APP_VERSION, COMPANY_NAME
from app.ui.pos_screen import PosScreen
from app.ui.dashboard import DashboardScreen
from app.ui.product_management import ProductManagementScreen
from app.ui.inventory_screen import InventoryScreen
from app.ui.supplier_screen import SupplierScreen
from app.ui.expense_screen import ExpenseScreen
from app.ui.customer_management import CustomerManagementScreen
from app.ui.operations_screen import OperationsScreen
from app.ui.reports import ReportsScreen
from app.ui.settings import SettingsScreen

from app.ui.theme_manager import get_theme_qss, LIGHT_THEME_QSS, DARK_THEME_QSS
from app.ui.backup_dialog import BackupDialog
CustomerScreen = CustomerManagementScreen

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
        QStatusBar, QMessageBox, QApplication, QPushButton
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QIcon, QKeySequence, QShortcut
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QMainWindow = object

if PYSIDE_AVAILABLE:
    class MainWindow(QMainWindow):
        def __init__(self, db_manager, repos, services, current_user=None):
            super().__init__()
            self.db_manager = db_manager
            self.repos = repos
            self.services = services
            self.current_user = current_user
            self.current_theme = "light"
            try:
                self.current_theme = self.repos["settings"].get_setting("app_theme", "light")
            except Exception:
                self.current_theme = "light"

            # Run automatic daily backup check once on launch
            try:
                if self.services and "backup" in self.services and self.services["backup"]:
                    self.services["backup"].check_and_run_daily_backup()
            except Exception as e:
                print(f"[Backup] Startup daily backup check notice: {e}")

            self.setWindowTitle(f"{COMPANY_NAME} - Desktop POS v{APP_VERSION}")
            self.resize(1280, 800)
            self.init_ui()
            self.setup_shortcuts()
            self.apply_theme(self.current_theme)

        def init_ui(self):
            central_widget = QWidget()
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # Top Header
            header = QWidget()
            header.setObjectName("headerWidget")
            h_layout = QHBoxLayout(header)
            h_layout.setContentsMargins(16, 10, 16, 10)

            title_box = QVBoxLayout()
            eng_title = QLabel(COMPANY_NAME)
            eng_title.setObjectName("headerTitle")
            urdu_title = QLabel("عروج کلوتھ اینڈ بیڈ شیٹ پردہ - کمپیوٹرائزڈ پوائنٹ آف سیل")
            urdu_title.setObjectName("headerUrdu")
            title_box.addWidget(eng_title)
            title_box.addWidget(urdu_title)
            h_layout.addLayout(title_box)

            h_layout.addStretch()

            # Header Actions: Backup & Theme Toggle
            self.backup_btn = QPushButton("💾 Backup")
            self.backup_btn.setObjectName("headerBackupBtn")
            self.backup_btn.setCursor(Qt.PointingHandCursor)
            self.backup_btn.setToolTip("Open Database Backup & Restore Manager (بیک اپ مینیجر)")
            self.backup_btn.clicked.connect(self.open_backup_dialog)
            h_layout.addWidget(self.backup_btn)
            h_layout.addSpacing(8)

            # Theme Toggle Button
            self.theme_btn = QPushButton("🌙 Dark" if self.current_theme == "light" else "☀️ Light")
            self.theme_btn.setObjectName("themeToggleBtn")
            self.theme_btn.setCursor(Qt.PointingHandCursor)
            self.theme_btn.setToolTip("Toggle Dark / Light Mode (تبدیل موڈ)")
            self.theme_btn.clicked.connect(self.toggle_theme)
            h_layout.addWidget(self.theme_btn)
            h_layout.addSpacing(16)

            # Right info in header: Offline status badge & Cashier profile
            info_box = QVBoxLayout()
            status_badge = QLabel("● Offline Local SQLite Database (Active)")
            status_badge.setStyleSheet("color: #86efac; font-weight: bold; font-size: 11px;")

            cashier_name = self.current_user.full_name if self.current_user else "Counter Staff"
            user_lbl = QLabel(f"Cashier: <b>{cashier_name}</b>")
            user_lbl.setStyleSheet("color: #f0fdf4; font-size: 13px;")

            info_box.addWidget(status_badge, alignment=Qt.AlignRight)
            info_box.addWidget(user_lbl, alignment=Qt.AlignRight)
            h_layout.addLayout(info_box)

            main_layout.addWidget(header)

            # Navigation Tabs
            self.tabs = QTabWidget()
            self.tabs.setDocumentMode(True)

            # Instantiate screens matching exact constructor signatures
            self.pos_screen = PosScreen(
                catalog_repo=self.repos["catalog"],
                sales_service=self.services["sales"],
                settings_repo=self.repos["settings"],
                current_user=self.current_user,
                customer_repo=self.repos["customer"]
            )

            self.stock_screen = ProductManagementScreen(
                catalog_repo=self.repos["catalog"],
                inventory_repo=self.repos["inventory"],
                user_id=self.current_user.id if self.current_user else 1
            )

            # Strictly pass inventory_repo, catalog_repo
            self.inventory_screen = InventoryScreen(
                inventory_repo=self.repos["inventory"],
                catalog_repo=self.repos["catalog"]
            )

            # Strictly pass supplier_repo, catalog_repo
            self.supplier_screen = SupplierScreen(
                supplier_repo=self.repos["supplier"],
                catalog_repo=self.repos["catalog"]
            )

            # Strictly pass expense_repo
            self.expense_screen = ExpenseScreen(
                expense_repo=self.repos["expense"]
            )

            # Strictly pass customer_repo
            self.customer_screen = CustomerManagementScreen(
                customer_repo=self.repos["customer"]
            )

            self.operations_screen = OperationsScreen(
                expense_repo=self.repos["expense"],
                supplier_repo=self.repos["supplier"],
                sales_repo=self.repos["sales"],
                catalog_repo=self.repos["catalog"],
                current_user=self.current_user
            )

            self.dashboard_screen = DashboardScreen(
                report_service=self.services["report"]
            )

            self.reports_screen = ReportsScreen(
                sales_repo=self.repos["sales"],
                settings_repo=self.repos["settings"]
            )

            self.settings_screen = SettingsScreen(
                settings_repo=self.repos["settings"],
                backup_service=self.services["backup"],
                user_repo=self.repos["user"],
                current_user=self.current_user
            )

            # Add Tabs with Bilingual Labels & Shortcut indicators
            self.tabs.addTab(self.pos_screen, "🛒 Billing [F1]")
            self.tabs.addTab(self.stock_screen, "📦 Products [F2]")
            self.tabs.addTab(self.inventory_screen, "📊 Stock [F3]")
            self.tabs.addTab(self.supplier_screen, "🏭 Suppliers [F4]")
            self.tabs.addTab(self.expense_screen, "💸 Expenses [F5]")
            self.tabs.addTab(self.customer_screen, "👥 Customers [F6]")
            self.tabs.addTab(self.operations_screen, "💵 Cash Shift [F7]")
            self.tabs.addTab(self.dashboard_screen, "📈 Dashboard [F8]")
            self.tabs.addTab(self.reports_screen, "🧾 Invoices [F9]")
            self.tabs.addTab(self.settings_screen, "⚙️ Settings [F10]")

            # Connect tab change to auto-refresh data
            self.tabs.currentChanged.connect(self.on_tab_changed)

            main_layout.addWidget(self.tabs)
            self.setCentralWidget(central_widget)

            # Status bar
            self.status_bar = QStatusBar()
            self.status_bar.showMessage("Shortcuts: F1=Billing | F2=Products | F3=Stock | F4=Suppliers | F5=Expenses | F6=Customers | F7=Shift Closing | F8=Dashboard | F9=Invoices | F10=Settings")
            self.setStatusBar(self.status_bar)

        def setup_shortcuts(self):
            # Function key navigation F1 through F10
            QShortcut(QKeySequence("F1"), self, lambda: self.tabs.setCurrentIndex(0))
            QShortcut(QKeySequence("F2"), self, lambda: self.tabs.setCurrentIndex(1))
            QShortcut(QKeySequence("F3"), self, lambda: self.tabs.setCurrentIndex(2))
            QShortcut(QKeySequence("F4"), self, lambda: self.tabs.setCurrentIndex(3))
            QShortcut(QKeySequence("F5"), self, lambda: self.tabs.setCurrentIndex(4))
            QShortcut(QKeySequence("F6"), self, lambda: self.tabs.setCurrentIndex(5))
            QShortcut(QKeySequence("F7"), self, lambda: self.tabs.setCurrentIndex(6))
            QShortcut(QKeySequence("F8"), self, lambda: self.tabs.setCurrentIndex(7))
            QShortcut(QKeySequence("F9"), self, lambda: self.tabs.setCurrentIndex(8))
            QShortcut(QKeySequence("F10"), self, lambda: self.tabs.setCurrentIndex(9))

        def on_tab_changed(self, index: int):
            if index == 0:
                self.pos_screen.load_products()
                if hasattr(self.pos_screen, "cart_widget") and hasattr(self.pos_screen.cart_widget, "load_customers"):
                    self.pos_screen.cart_widget.load_customers()
                if hasattr(self.pos_screen, "barcode_input"):
                    self.pos_screen.barcode_input.setFocus()
            elif index == 1:
                self.stock_screen.load_products()
            elif index == 2:
                self.inventory_screen.load_data()
            elif index == 3:
                self.supplier_screen.load_data()
            elif index == 4:
                self.expense_screen.load_expenses()
            elif index == 5:
                self.customer_screen.load_customers()
            elif index == 6:
                self.operations_screen.refresh_all()
            elif index == 7:
                self.dashboard_screen.load_data()
            elif index == 8:
                self.reports_screen.load_invoices()
            elif index == 9:
                self.settings_screen.load_settings()

        def apply_theme(self, theme_name: str):
            """Applies QSS stylesheet and updates button label."""
            self.current_theme = "dark" if theme_name == "dark" else "light"
            qss = get_theme_qss(self.current_theme)
            app_inst = QApplication.instance()
            if app_inst:
                app_inst.setStyleSheet(qss)
            else:
                self.setStyleSheet(qss)

            if hasattr(self, "theme_btn"):
                self.theme_btn.setText("☀️ Light" if self.current_theme == "dark" else "🌙 Dark")

        def toggle_theme(self):
            """Toggles between Dark Mode (#1e1e1e) and Light Mode (#f8f9fa)."""
            new_theme = "dark" if self.current_theme == "light" else "light"
            self.apply_theme(new_theme)
            try:
                self.repos["settings"].set_setting("app_theme", new_theme)
            except Exception:
                pass

        def open_backup_dialog(self):
            """Opens the full Database Backup & Restore Manager dialog."""
            backup_service = self.services.get("backup") if self.services else None
            if not backup_service:
                QMessageBox.warning(self, "Backup Unavailable", "Database backup service is not initialized.")
                return
            dlg = BackupDialog(backup_service=backup_service, parent=self)
            dlg.exec()
else:
    class MainWindow:
        def __init__(self, db_manager=None, repos=None, services=None, current_user=None, *args, **kwargs):
            self.db_manager = db_manager
            self.repos = repos or {}
            self.services = services or {}
            self.current_user = current_user
            self.current_theme = "light"
