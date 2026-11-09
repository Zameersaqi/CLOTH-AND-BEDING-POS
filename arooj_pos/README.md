# Arooj Cloth and Bedsheet Parda - Desktop POS Software
### Complete Offline Windows Retail POS System (Python & PySide6)

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6.svg)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB.svg)](https://python.org)
[![Database](https://img.shields.io/badge/Database-SQLite%20(Local%20WAL)-003B57.svg)](https://sqlite.org)
[![Currency](https://img.shields.io/badge/Currency-PKR%20(Rs.)-059669.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-darkgreen.svg)]()

A complete, production-grade Windows desktop Point of Sale (POS) application built exclusively in **Python** for **Arooj Cloth and Bedsheet Parda** (clothing, bedding, curtains, fabric, and home textile retail in Pakistan).

The application is 100% offline, stores all data locally in SQLite, includes a rich preloaded Pakistani textile catalog, provides fast touch-friendly visual product cards, supports editable customer-negotiated prices in the cart, prints 58mm/80mm thermal receipts, and is packaged with **PyInstaller** and **Inno Setup** into `Arooj_POS_Setup.exe`.

---

## 🌟 Key Features

1. **100% Offline & Local Data Ownership**:
   - Zero cloud subscription, no mandatory internet connection, and zero telemetry.
   - Powered by SQLite with Write-Ahead Logging (WAL) and strict ACID foreign-key enforcement.
   - User data, database, backups, and custom logo are stored in `%LOCALAPPDATA%\AroojPOS`, surviving software upgrades and reinstalls.

2. **Preloaded Textile & Bedding Catalog**:
   - Automatically initializes with 16 retail textile categories and 36 editable product templates:
     - **Razai**: Single, Double, King, Queen, Cotton, Winter Heavy, Lightweight AC Razai
     - **Kambal & AC Kambal**: 1-ply, 2-ply Korean Mink, Summer Fleece, Flannel
     - **Khais**: Multani traditional handloom, dense cotton weave
     - **Bedsheets**: King/Queen/Single sets with pillow covers, satin stripe, cotton percale
     - **Bridal Razai Sets**: 6-piece and 8-piece luxury velvet/zari embroidered sets
     - **Cushions & Covers**: 16x16 / 18x18 filled cushions, covers, ethnic printed sets
     - **Abayas**: Front-open, closed, party wear, crepe Nida with matching scarf
     - **Ladies Suiting**: 2-piece / 3-piece stitched lawn, unstitched fabric by meter & suit cut
     - **Gents Cloth**: Box-packed latha & wash-and-wear, fabric thaans sold by meter/yard
     - **Curtains & Parda**: Ready-made eyelet ring panels (7ft/9ft), velvet parda by meter
     - **Scarves & Stoles**: Turkish silk squares, crinkle chiffon, pashmina & woolen stoles
   - Idempotent seed data: Reopening the app never duplicates categories or overwrites user prices/stock.

3. **Visual Product-Card Billing Screen**:
   - Large touch-and-click product cards with category filters, barcode scanner input, and search bar.
   - Compact variant selector for choosing size, color, design, and fabric cut length (meters/yards).

4. **Editable Cart Prices (Customer Negotiation)**:
   - Cashiers can edit transaction selling prices directly in the cart without altering the master catalog price.
   - Enforces cashier discount thresholds (e.g. max 15%); steep discounts require a Manager PIN.
   - Clear visual badge on cart items when price differs from master catalog price.
   - Instant Decimal-based recomputation of subtotals, taxes, and grand totals.

5. **58mm & 80mm Thermal Receipt Printing**:
   - Monospaced column-aligned plain text, ESC/POS byte sequences, and HTML preview.
   - Header with Shop Name in English and Urdu (`عروج کلوتھ اینڈ بیڈ شیٹ پردہ`), address, phone, invoice number.
   - Line items with quantities, units, negotiated prices, subtotal, discounts, tax, cash tendered, and change given.
   - Reprint saved receipts at any time without duplicating sales.

6. **Inventory, Fabric Rolls (Thaans) & Purchasing**:
   - Track fabric rolls with individual roll numbers, starting length, and current remaining length.
   - Decimal quantity deductions for meters and yards.
   - Stock adjustments with audit reason and user tracking.
   - Low-stock alerts and inventory valuation (cost vs retail).

7. **Customer Ledger & Credit Sales**:
   - Customer accounts with phone, address, and credit limits.
   - Record partial cash payments at billing with remaining amount automatically posted to customer ledger.
   - Direct balance payment receipt workflow (without creating fake sales).

8. **Financial Reports & Dashboard**:
   - Real-time revenue, Cost of Goods Sold (COGS), Gross Profit, Shop Expenses, and Net Profit.
   - Outstanding customer receivables and supplier payables.
   - Sales breakdown by category and top-selling products.

9. **Data Safety, Backup & Restore**:
   - SQLite online live backup API snapshots database to timestamped `.db` files without blocking checkout.
   - One-click backup to custom folder or USB flash drive.
   - Verified restoration with automated pre-restore safety snapshot.

---

## 📁 Project Structure

```
arooj_pos/
├── main.py                      # Application entry point (GUI / CLI verification)
├── requirements.txt             # Tested pinned dependencies
├── README.md                    # Complete project documentation
├── .gitignore                   # Git ignore patterns
├── build_windows.bat            # One-click Windows build script (PyInstaller + Inno Setup)
├── arooj_pos.spec               # PyInstaller standalone executable spec
├── installer/
│   └── Arooj_POS_Setup.iss      # Inno Setup Windows installer script
├── app/
│   ├── __init__.py
│   ├── config.py                # Paths, Decimal currency helpers, defaults
│   ├── database.py              # SQLite connection, WAL mode, foreign keys, backup API
│   ├── migrations/              # Schema migration runner
│   │   ├── __init__.py
│   │   └── _001_initial_schema.py
│   ├── models/                  # Typed domain entities
│   │   ├── __init__.py
│   │   └── entities.py
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py
│   │   ├── catalog_repository.py
│   │   ├── sales_repository.py
│   │   ├── inventory_repository.py
│   │   ├── customer_repository.py
│   │   ├── supplier_repository.py
│   │   ├── expense_repository.py
│   │   ├── user_repository.py
│   │   └── settings_repository.py
│   ├── services/                # Business logic & services
│   │   ├── __init__.py
│   │   ├── sales_service.py     # Cart logic, price overrides, PIN checks, checkout
│   │   ├── printer_service.py   # 58mm & 80mm thermal receipt generator
│   │   ├── report_service.py    # Revenue, COGS, gross/net profit, valuation
│   │   ├── backup_service.py    # SQLite online snapshots & restoration
│   │   ├── auth_service.py      # Session & authentication
│   │   └── catalog_service.py   # Inventory & customer services
│   ├── ui/                      # PySide6 desktop interface
│   │   ├── __init__.py
│   │   ├── main_window.py       # Master window with bilingual header & shortcuts
│   │   ├── pos_screen.py        # Visual billing screen
│   │   ├── product_cards.py     # Product card grid & variant selector
│   │   ├── cart_widget.py       # Cart table with editable prices & checkout
│   │   ├── dashboard.py         # Real-time metrics cards
│   │   ├── product_management.py# Stock and fabric thaan manager
│   │   ├── customer_management.py# Customer ledger and payment receipts
│   │   ├── reports.py           # Invoices list and thermal receipt reprint
│   │   ├── settings.py          # Shop profile, logo upload, printer width
│   │   └── setup_wizard.py      # First-run onboarding dialog
│   ├── resources/
│   │   └── styles/
│   │       └── pos_theme.qss    # Emerald & gold Pakistani retail theme
│   └── seed/
│       ├── __init__.py
│       └── initial_catalog.py   # Full preloaded Pakistani textile catalog
└── tests/                       # Automated test suite (Python unittest stdlib)
    ├── __init__.py
    ├── run_tests.py             # Test runner script
    ├── test_database.py         # Tables, WAL mode, foreign keys, rollback
    ├── test_catalog_seed.py     # Category completeness & idempotency
    ├── test_sales_cart.py       # Cart, totals, payments, invoice numbers
    ├── test_editable_prices.py  # Negotiated prices, PIN override, catalog isolation
    ├── test_inventory_fabric.py # Meters/yards, thaan roll deduction
    ├── test_customer_ledger.py  # Credit sales, ledger statements, balance
    ├── test_reports_profit.py   # COGS, gross & net profit, valuation
    └── test_backup_restore.py   # SQLite backup and restoration cycle
```

---

## 🚀 Getting Started on Windows

### Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.10 or 3.11 installed from [python.org](https://www.python.org/) (check **"Add Python to PATH"** during install)

### 1. Quick Setup & Run in Development
Open PowerShell or Command Prompt in the `arooj_pos` folder:

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate virtual environment
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run automated test suite
python tests\run_tests.py

# 5. Launch the POS application
python main.py
```

### 2. Verify Database & Catalog via CLI
To verify the offline database, schema, and preloaded seed catalog without launching the GUI:

```bash
python main.py --verify
```

---

## 🛠️ Building Standalone Windows Executable & Installer

### Automatic Build
Double-click `build_windows.bat` in the project root. The script will:
1. Verify Python installation
2. Create and activate `.venv`
3. Install pinned dependencies from `requirements.txt`
4. Run all 14 automated unit tests
5. Package the application with **PyInstaller** into `dist\Arooj_POS\`
6. Compile the **Inno Setup** script into `dist\Arooj_POS_Setup.exe`

### Manual Step-by-Step Build
```bash
# Compile with PyInstaller
pyinstaller --noconfirm --clean arooj_pos.spec

# Compile Inno Setup Installer (if Inno Setup is installed)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\Arooj_POS_Setup.iss
```

The resulting `dist\Arooj_POS_Setup.exe` can be distributed to shop computers. When installed, it creates Desktop and Start Menu shortcuts and configures uninstallation without deleting shop transaction databases or backups.

---

## 🧪 Automated Testing Report

The codebase includes 34 comprehensive automated unit tests using Python's standard `unittest` library (requiring zero external packages to test):

```bash
python tests/run_tests.py
```

**Test Coverage Summary (34/34 Tests Passed):**
- `test_database`: Validates schema migrations, table creation, foreign keys, and transaction rollbacks.
- `test_catalog_seed`: Validates preloading of all 16 categories, subcategories, units, and verifies 100% idempotency.
- `test_sales_cart`: Validates cart calculations, sequential invoice numbering (`INV-YYYYMMDD-XXXX`), cash change due.
- `test_editable_prices`: Validates that customer-negotiated cart prices do NOT mutate the master catalog, enforces cashier discount limits, requires Manager PIN for overrides, and blocks negative rates.
- `test_inventory_fabric`: Validates decimal length cuts (meters/yards) and tracks fabric roll (thaan) remaining lengths.
- `test_customer_ledger`: Validates credit sales, running balance ledgers, and payment receipts without fake sales.
- `test_reports_profit`: Validates exact COGS, Gross Profit, recorded Expenses, and Net Profit calculations.
- `test_backup_restore`: Validates SQLite online live backup snapshots, integrity checking, and safe database recovery.
- `test_bulk_import`: Validates CSV/Excel parsing, duplicate SKU detection, unit normalization (`MTR`, `YD`/`GAZ`, `PCS`, `SET`, `ROLL`), conflict policies (`add_new_only`, `update_existing`, `skip_existing`), transaction safety, and catalog CSV export.
- `test_real_printing`: Validates printer discovery list, 58mm vs 80mm column width formatting, duplicate reprint watermarks, local receipt spooling to `%LOCALAPPDATA%\AroojPOS\receipts\`, and accurate error reporting.
- `test_auth_security`: Validates PBKDF2 HMAC SHA-256 password hashing with unique 16-byte random salts, user login, secure password change verifying old password, and manager PIN checks.
- `test_cash_register`: Validates cash drawer shift reconciliations (opening float + cash sales - cash expenses = expected cash), balanced/excess/shortage tracking, and supplier purchase bills with ledger balance updates.

---

## 🏢 Business Operations & Default Credentials

- **Default Admin Username**: `admin`
- **Default Admin Password**: `admin` *(Change in First-Run Wizard or Settings)*
- **Default Manager PIN**: `1234` *(Used for price override authorizations)*
- **Receipt Paper Width**: `80mm` or `58mm` (Selectable in Settings)
- **Local Database Location**:
  - Windows: `%LOCALAPPDATA%\AroojPOS\arooj_pos.db`
  - Linux/Mac: `~/.arooj_pos/arooj_pos.db`
- **Backups Location**: `%LOCALAPPDATA%\AroojPOS\backups\`
- **Receipt Spool Archive**: `%LOCALAPPDATA%\AroojPOS\receipts\`
- **Import Templates**: `resources/templates/product_import_template.csv` and `sample_products_import.csv`
