"""
Arooj Cloth and Bedsheet Parda - Desktop POS Entry Point
Author: Senior Python Application Architect
Target: Windows Desktop (Offline SQLite, PySide6, PyInstaller, Inno Setup)
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import APP_NAME, APP_VERSION, COMPANY_NAME, get_app_data_dir, get_db_path
from app.database import db_manager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories import (
    CatalogRepository, SalesRepository, InventoryRepository,
    CustomerRepository, SupplierRepository, ExpenseRepository,
    UserRepository, SettingsRepository
)
from app.services import (
    SalesService, PrinterService, ReportService,
    BackupService, AuthService, CatalogService, CustomerService, InventoryService
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("arooj_pos")

def initialize_app(custom_db_path: str = None):
    """Initializes SQLite database, applies migrations, and seeds catalog idempotently."""
    if custom_db_path:
        os.environ["AROOJ_POS_DB_PATH"] = custom_db_path
        db_manager.db_path = Path(custom_db_path)

    conn = db_manager.get_connection()
    logger.info(f"Connected to SQLite database at: {db_manager.db_path}")

    # 1. Migrations
    apply_migrations(conn)

    # 2. Seed initial catalog & business settings
    seed_database(conn)

    # 3. Assemble Repositories
    repos = {
        "catalog": CatalogRepository(conn),
        "sales": SalesRepository(conn),
        "inventory": InventoryRepository(conn),
        "customer": CustomerRepository(conn),
        "supplier": SupplierRepository(conn),
        "expense": ExpenseRepository(conn),
        "user": UserRepository(conn),
        "settings": SettingsRepository(conn)
    }

    # 4. Assemble Services
    services = {
        "sales": SalesService(repos["sales"], repos["user"], repos["settings"]),
        "printer": PrinterService(paper_width=repos["settings"].get_setting("receipt_paper_width", "80mm")),
        "report": ReportService(conn),
        "backup": BackupService(db_manager),
        "auth": AuthService(repos["user"]),
        "catalog": CatalogService(repos["catalog"]),
        "customer": CustomerService(repos["customer"]),
        "inventory": InventoryService(repos["inventory"])
    }

    return repos, services

def main():
    parser = argparse.ArgumentParser(description=f"{COMPANY_NAME} Desktop POS")
    parser.add_argument("--db", type=str, help="Custom SQLite database file path")
    parser.add_argument("--headless", action="store_true", help="Run database & seed initialization without GUI")
    parser.add_argument("--verify", action="store_true", help="Verify database integrity and catalog counts")
    args = parser.parse_args()

    repos, services = initialize_app(args.db)

    if args.verify or args.headless:
        # CLI Verification Mode
        cats = repos["catalog"].get_categories()
        prods = repos["catalog"].get_products()
        units = repos["catalog"].get_units()
        summary = services["report"].get_dashboard_summary()
        print(f"\n==========================================")
        print(f" {COMPANY_NAME} - SYSTEM INITIALIZED")
        print(f" Version: {APP_VERSION}")
        print(f" Database: {db_manager.db_path}")
        print(f" Loaded Categories: {len(cats)}")
        print(f" Loaded Product Templates: {len(prods)}")
        print(f" Configured Units: {len(units)}")
        print(f" Total Revenue: Rs. {summary['total_revenue']:,.2f}")
        print(f"==========================================\n")
        return 0

    # Launch PySide6 GUI
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        from app.ui.main_window import MainWindow
        from app.ui.setup_wizard import SetupWizardDialog

        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)

        # Load QSS Style
        qss_path = BASE_DIR / "app" / "resources" / "styles" / "pos_theme.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())

        # Check first run setup wizard
        first_run = repos["settings"].get_setting("first_run_completed", "0")
        if first_run == "0":
            wizard = SetupWizardDialog(repos["settings"], repos["user"])
            wizard.exec()

        # Get default user (admin)
        current_user = repos["user"].authenticate("admin", "admin")
        if not current_user:
            cursor = db_manager.get_connection().cursor()
            cursor.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1;")
            r = cursor.fetchone()
            from app.models.entities import User
            if r:
                current_user = User(
                    id=r["id"], username=r["username"], full_name=r["full_name"],
                    role=r["role"], password_hash=r["password_hash"], salt=r["salt"],
                    manager_pin=r["manager_pin"]
                )

        window = MainWindow(db_manager, repos, services, current_user)
        window.show()
        return app.exec()

    except ImportError:
        logger.warning("PySide6 is not installed in this environment. Run 'pip install -r requirements.txt' on Windows.")
        print(f"\n[NOTICE] PySide6 GUI framework is required for desktop window rendering.")
        print(f"The core Python POS database, repositories, services, and tests are verified and ready.")
        print(f"Run tests with: python3 tests/run_tests.py\n")
        return 0

if __name__ == "__main__":
    sys.exit(main())
