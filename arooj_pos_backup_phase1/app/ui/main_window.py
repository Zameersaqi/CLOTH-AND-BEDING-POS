"""
Main Application Window for Arooj Cloth and Bedsheet Parda Desktop POS
"""

import sys
from pathlib import Path
from app.config import APP_NAME, APP_VERSION, COMPANY_NAME
from app.ui.pos_screen import PosScreen
from app.ui.dashboard import DashboardScreen
from app.ui.product_management import ProductManagementScreen
from app.ui.customer_management import CustomerManagementScreen
from app.ui.reports import ReportsScreen
from app.ui.settings import SettingsScreen

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
        QStatusBar, QMessageBox, QApplication
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

            self.setWindowTitle(f"{COMPANY_NAME} - Desktop POS v{APP_VERSION}")
            self.resize(1280, 800)
            self.init_ui()
            self.setup_shortcuts()

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
            self.tabs.setStyleSheet("""
                QTabBar::tab {
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 700;
                    color: #334155;
                }
                QTabBar::tab:selected {
                    color: #064e3b;
                    border-bottom: 3px solid #059669;
                    background: #ecfdf5;
                }
            """)

            # Instantiate screens
            self.pos_screen = PosScreen(
                catalog_repo=self.repos["catalog"],
                sales_service=self.services["sales"],
                settings_repo=self.repos["settings"],
                current_user=self.current_user
            )

            self.stock_screen = ProductManagementScreen(
                catalog_repo=self.repos["catalog"],
                inventory_repo=self.repos["inventory"],
                user_id=self.current_user.id if self.current_user else 1
            )

            self.customer_screen = CustomerManagementScreen(
                customer_repo=self.repos["customer"]
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
                backup_service=self.services["backup"]
            )

            # Add Tabs with Bilingual Labels
            self.tabs.addTab(self.pos_screen, "🛒 POS Billing (بلنگ)")
            self.tabs.addTab(self.stock_screen, "📦 Stock & Catalog (سٹاک)")
            self.tabs.addTab(self.customer_screen, "👥 Customer Ledger (کھاتہ جات)")
            self.tabs.addTab(self.dashboard_screen, "📊 Dashboard (ڈیش بورڈ)")
            self.tabs.addTab(self.reports_screen, "🧾 Invoices & Reports (انوائسز)")
            self.tabs.addTab(self.settings_screen, "⚙️ Settings (ترتیبات)")

            # Connect tab change to auto-refresh data
            self.tabs.currentChanged.connect(self.on_tab_changed)

            main_layout.addWidget(self.tabs)
            self.setCentralWidget(central_widget)

            # Status bar
            self.status_bar = QStatusBar()
            self.status_bar.showMessage("Ready. Fast Shortcuts: F1=Billing | F2=Stock | F3=Ledger | F4=Dashboard | F10=Complete Sale")
            self.setStatusBar(self.status_bar)

        def setup_shortcuts(self):
            # Function key navigation
            QShortcut(QKeySequence("F1"), self, lambda: self.tabs.setCurrentIndex(0))
            QShortcut(QKeySequence("F2"), self, lambda: self.tabs.setCurrentIndex(1))
            QShortcut(QKeySequence("F3"), self, lambda: self.tabs.setCurrentIndex(2))
            QShortcut(QKeySequence("F4"), self, lambda: self.tabs.setCurrentIndex(3))
            QShortcut(QKeySequence("F5"), self, lambda: self.tabs.setCurrentIndex(4))

        def on_tab_changed(self, index: int):
            if index == 0:
                self.pos_screen.load_products()
            elif index == 1:
                self.stock_screen.load_products()
            elif index == 2:
                self.customer_screen.load_customers()
            elif index == 3:
                self.dashboard_screen.load_data()
            elif index == 4:
                self.reports_screen.load_invoices()
else:
    class MainWindow:
        pass
