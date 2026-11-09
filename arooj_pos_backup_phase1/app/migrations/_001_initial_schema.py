"""
Migration 001: Complete Initial Schema for Arooj Cloth and Bedsheet Parda
Includes categories, units, products, variants, fabric rolls, customers, suppliers,
sales, sale items, payments, held sales, purchases, stock movements, ledgers,
expenses, cash registers, users, audit logs, and business settings.
"""

import sqlite3

def run_migration_001(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # 1. Categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_urdu TEXT,
            description TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Subcategories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            name_urdu TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
            UNIQUE (category_id, code)
        );
    """)

    # 3. Units
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            is_decimal INTEGER DEFAULT 0,
            symbol TEXT NOT NULL
        );
    """)

    # 4. Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            subcategory_id INTEGER,
            code TEXT UNIQUE NOT NULL,
            barcode TEXT,
            name TEXT NOT NULL,
            name_urdu TEXT,
            unit_id INTEGER NOT NULL,
            is_template INTEGER DEFAULT 0,
            is_fabric INTEGER DEFAULT 0,
            min_stock_alert REAL DEFAULT 5.0,
            base_cost_price REAL DEFAULT 0.0,
            base_selling_price REAL DEFAULT 0.0,
            description TEXT,
            image_path TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories (id),
            FOREIGN KEY (unit_id) REFERENCES units (id)
        );
    """)

    # 5. Product Variants
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            barcode TEXT,
            size TEXT,
            color TEXT,
            design TEXT,
            fabric_type TEXT,
            dimensions TEXT,
            weight_grams REAL,
            cost_price REAL DEFAULT 0.0,
            selling_price REAL DEFAULT 0.0,
            stock_quantity REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        );
    """)

    # 6. Fabric Rolls (Thaans)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fabric_rolls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variant_id INTEGER,
            roll_number TEXT UNIQUE NOT NULL,
            initial_length REAL NOT NULL,
            current_length REAL NOT NULL,
            unit_name TEXT DEFAULT 'Meter',
            cost_per_unit REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (variant_id) REFERENCES product_variants (id)
        );
    """)

    # 7. Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            city TEXT DEFAULT 'Local',
            credit_limit REAL DEFAULT 50000.0,
            opening_balance REAL DEFAULT 0.0,
            current_balance REAL DEFAULT 0.0,
            discount_percent REAL DEFAULT 0.0,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 8. Suppliers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            address TEXT,
            opening_balance REAL DEFAULT 0.0,
            current_balance REAL DEFAULT 0.0,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 9. Sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            cashier_id INTEGER,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL NOT NULL,
            discount_amount REAL DEFAULT 0.0,
            discount_percent REAL DEFAULT 0.0,
            tax_amount REAL DEFAULT 0.0,
            grand_total REAL NOT NULL,
            paid_amount REAL NOT NULL,
            balance_amount REAL DEFAULT 0.0,
            payment_status TEXT NOT NULL,
            payment_method TEXT DEFAULT 'Cash',
            notes TEXT,
            is_returned INTEGER DEFAULT 0,
            return_ref_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        );
    """)

    # 10. Sale Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            variant_id INTEGER,
            roll_id INTEGER,
            quantity REAL NOT NULL,
            unit_name TEXT NOT NULL,
            original_catalog_price REAL NOT NULL,
            transaction_price REAL NOT NULL,
            line_discount REAL DEFAULT 0.0,
            line_total REAL NOT NULL,
            cost_price REAL DEFAULT 0.0,
            is_price_overridden INTEGER DEFAULT 0,
            override_reason TEXT,
            override_approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (variant_id) REFERENCES product_variants (id),
            FOREIGN KEY (roll_id) REFERENCES fabric_rolls (id)
        );
    """)

    # 11. Sale Payments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            amount REAL NOT NULL,
            tendered_amount REAL DEFAULT 0.0,
            change_returned REAL DEFAULT 0.0,
            reference_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE
        );
    """)

    # 12. Held Sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS held_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hold_code TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            cart_payload_json TEXT NOT NULL,
            hold_note TEXT,
            cashier_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 13. Purchases
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_invoice_no TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL NOT NULL,
            tax_amount REAL DEFAULT 0.0,
            grand_total REAL NOT NULL,
            paid_amount REAL NOT NULL,
            balance_amount REAL DEFAULT 0.0,
            payment_status TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        );
    """)

    # 14. Purchase Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            variant_id INTEGER,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_id) REFERENCES purchases (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (variant_id) REFERENCES product_variants (id)
        );
    """)

    # 15. Stock Movement Ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variant_id INTEGER,
            roll_id INTEGER,
            transaction_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            reference_id INTEGER,
            reference_type TEXT,
            unit_cost REAL DEFAULT 0.0,
            notes TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (variant_id) REFERENCES product_variants (id),
            FOREIGN KEY (roll_id) REFERENCES fabric_rolls (id)
        );
    """)

    # 16. Customer Ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            sale_id INTEGER,
            transaction_type TEXT NOT NULL,
            debit REAL DEFAULT 0.0,
            credit REAL DEFAULT 0.0,
            running_balance REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (sale_id) REFERENCES sales (id)
        );
    """)

    # 17. Supplier Ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            purchase_id INTEGER,
            transaction_type TEXT NOT NULL,
            debit REAL DEFAULT 0.0,
            credit REAL DEFAULT 0.0,
            running_balance REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
            FOREIGN KEY (purchase_id) REFERENCES purchases (id)
        );
    """)

    # 18. Expenses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'Cash',
            description TEXT,
            receipt_ref TEXT,
            recorded_by INTEGER,
            expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 19. Cash Registers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cash_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cashier_id INTEGER NOT NULL,
            shift_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shift_end TIMESTAMP,
            opening_cash REAL NOT NULL,
            total_cash_sales REAL DEFAULT 0.0,
            total_cash_returns REAL DEFAULT 0.0,
            total_expenses REAL DEFAULT 0.0,
            cash_in REAL DEFAULT 0.0,
            cash_out REAL DEFAULT 0.0,
            expected_cash REAL DEFAULT 0.0,
            actual_cash REAL,
            discrepancy REAL,
            notes TEXT,
            status TEXT DEFAULT 'open'
        );
    """)

    # 20. Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            manager_pin TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 21. Audit Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity TEXT NOT NULL,
            entity_id TEXT,
            details TEXT,
            ip_or_machine TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 22. Business Settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            data_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Essential Indexes for high-performance retail lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_variants_product ON product_variants(product_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_variants_barcode ON product_variants(barcode);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_trans_prod ON stock_transactions(product_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cust_ledger_cust ON customer_ledger(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supp_ledger_supp ON supplier_ledger(supplier_id);")
