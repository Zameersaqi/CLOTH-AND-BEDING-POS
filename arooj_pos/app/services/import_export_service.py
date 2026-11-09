"""
Import & Export Service for Arooj Cloth and Bedsheet Parda
Supports bulk Excel (.xlsx) and CSV import/export of products, variants, units, and categories.
Features:
- Downloadable templates with clear headers and textile examples
- Row-level validation, duplicate detection, invalid unit warnings
- Modes: 'add_new_only', 'update_existing', 'skip_existing'
- Atomic transaction safety (zero corruption on failure)
- Comprehensive summary with added, updated, skipped, failed counts
"""

import csv
import os
import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.config import to_decimal, to_qty_decimal
from app.models.entities import Product, ProductVariant

SUPPORTED_UNITS_MAP = {
    "piece": "PCS",
    "pcs": "PCS",
    "pc": "PCS",
    "set": "SET",
    "sets": "SET",
    "pair": "PAIR",
    "pairs": "PAIR",
    "pr": "PAIR",
    "meter": "MTR",
    "meters": "MTR",
    "mtr": "MTR",
    "m": "MTR",
    "yard": "YD",
    "yards": "YD",
    "yd": "YD",
    "gaz": "YD",
    "guz": "YD",
    "roll": "ROLL",
    "rolls": "ROLL",
    "thaan": "ROLL",
    "than": "ROLL",
    "pack": "PACK",
    "packs": "PACK",
    "pk": "PACK",
    "kg": "KG",
    "kilogram": "KG",
    "kgs": "KG",
    "gram": "GM",
    "grams": "GM",
    "gm": "GM",
    "g": "GM"
}

TEMPLATE_COLUMNS = [
    "category",
    "subcategory",
    "product_name",
    "product_name_urdu",
    "sku",
    "barcode",
    "unit",
    "size",
    "color",
    "design",
    "fabric_type",
    "dimensions",
    "purchase_price",
    "selling_price",
    "opening_stock",
    "min_stock_alert"
]

IMPORT_HEADERS = TEMPLATE_COLUMNS

SAMPLE_RECORDS = [
    {
        "category": "Razai",
        "subcategory": "Double Razai",
        "product_name": "Winter Heavy Quilted Razai",
        "product_name_urdu": "سردیوں کی بھاری رضائی",
        "sku": "IMP-RZ-001",
        "barcode": "8961001001",
        "unit": "Piece",
        "size": "Double",
        "color": "Maroon Gold",
        "design": "Embossed Quilt",
        "fabric_type": "Microfiber Cotton",
        "dimensions": "90x100 in",
        "purchase_price": "2600.00",
        "selling_price": "4200.00",
        "opening_stock": "15",
        "min_stock_alert": "3"
    },
    {
        "category": "Bedsheets",
        "subcategory": "King Bedsheet",
        "product_name": "Luxury Cotton 3-Piece Bedsheet Set",
        "product_name_urdu": "کاٹن بیڈ شیٹ سیٹ مع تکیے",
        "sku": "IMP-BS-001",
        "barcode": "8961001002",
        "unit": "Set",
        "size": "King",
        "color": "Royal Navy",
        "design": "Stripe Percale",
        "fabric_type": "100% Pure Cotton",
        "dimensions": "100x108 in",
        "purchase_price": "1400.00",
        "selling_price": "2400.00",
        "opening_stock": "30",
        "min_stock_alert": "5"
    },
    {
        "category": "Gents Cloth",
        "subcategory": "Suiting Thaan",
        "product_name": "Premium Wash & Wear Suiting Fabric",
        "product_name_urdu": "مردانہ واش اینڈ ویئر تھان فی میٹر",
        "sku": "IMP-GC-001",
        "barcode": "8961001003",
        "unit": "Meter",
        "size": "Per Meter",
        "color": "Charcoal Grey",
        "design": "Matte Solid",
        "fabric_type": "Wash and Wear",
        "dimensions": "Width 54 in",
        "purchase_price": "350.00",
        "selling_price": "650.00",
        "opening_stock": "80",
        "min_stock_alert": "20"
    },
    {
        "category": "Curtains & Parda",
        "subcategory": "Ready-Made Curtains",
        "product_name": "Blackout Eyelet Ring Curtain Panel",
        "product_name_urdu": "ریڈی میڈ پردہ آئیلٹ پینل",
        "sku": "IMP-CP-001",
        "barcode": "8961001004",
        "unit": "Piece",
        "size": "7 Ft (84 in)",
        "color": "Beige Cream",
        "design": "Jacquard Textured",
        "fabric_type": "Heavy Polyester",
        "dimensions": "54x84 in",
        "purchase_price": "1100.00",
        "selling_price": "1850.00",
        "opening_stock": "20",
        "min_stock_alert": "4"
    },
    {
        "category": "Abayas",
        "subcategory": "Front-Open Abaya",
        "product_name": "Classic Black Front-Open Nida Abaya",
        "product_name_urdu": "بلیک فرنٹ اوپن ندا عبایا",
        "sku": "IMP-AB-001",
        "barcode": "8961001005",
        "unit": "Piece",
        "size": "54",
        "color": "Jet Black",
        "design": "Lace Sleeve",
        "fabric_type": "Korean Nida",
        "dimensions": "Length 54 in",
        "purchase_price": "2200.00",
        "selling_price": "3800.00",
        "opening_stock": "12",
        "min_stock_alert": "2"
    }
]


class ImportExportService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def generate_csv_template(self, file_path: str, include_samples: bool = False):
        """Generates an editable CSV template with standardized headers and optional sample records."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TEMPLATE_COLUMNS)
            writer.writeheader()
            if include_samples:
                for row in SAMPLE_RECORDS:
                    writer.writerow(row)

    def generate_excel_template(self, file_path: str, include_samples: bool = False):
        """Generates an Excel (.xlsx) template if openpyxl is installed, fallback to CSV if not."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Arooj Product Import"

            # Header styling
            header_fill = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid")
            header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            border = Border(
                left=Side(style="thin", color="CCCCCC"),
                right=Side(style="thin", color="CCCCCC"),
                top=Side(style="thin", color="CCCCCC"),
                bottom=Side(style="thin", color="CCCCCC")
            )

            ws.append(TEMPLATE_COLUMNS)
            for col_num in range(1, len(TEMPLATE_COLUMNS) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border

            if include_samples:
                for row_data in SAMPLE_RECORDS:
                    row_values = [row_data.get(c, "") for c in TEMPLATE_COLUMNS]
                    ws.append(row_values)

            # Adjust column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

            wb.save(file_path)
        except ImportError:
            # Fallback to CSV if openpyxl is not installed
            csv_path = str(Path(file_path).with_suffix(".csv"))
            self.generate_csv_template(csv_path, include_samples)

    def parse_file(self, file_path: str) -> List[Dict[str, str]]:
        """Parses CSV or Excel file into a list of row dictionaries."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        rows = []
        if path.suffix.lower() in (".xlsx", ".xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True)
                ws = wb.active
                headers = []
                for i, row in enumerate(ws.iter_rows(values_only=True)):
                    if i == 0:
                        headers = [str(cell or "").strip().lower() for cell in row]
                    else:
                        if not any(row):
                            continue
                        row_dict = {}
                        for h, val in zip(headers, row):
                            row_dict[h] = "" if val is None else str(val).strip()
                        rows.append(row_dict)
            except ImportError:
                raise RuntimeError("openpyxl is required to parse .xlsx files. Please install openpyxl or import as .csv.")
        else:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cleaned = {k.strip().lower(): (v.strip() if v else "") for k, v in r.items() if k}
                    if any(cleaned.values()):
                        rows.append(cleaned)

        return rows

    def validate_and_parse_csv(self, file_path: str, mode: str = "add_new_only"):
        """Convenience method returning (valid_rows, list_of_error_strings)."""
        self._last_parsed_file = file_path
        res = self.validate_and_import(file_path, mode=mode, commit=False)
        errors = [f"Row {e['row']}: {e['message']}" for e in res["errors"]]
        class ImportedRow:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
                self.unit = d.get("unit_code", "")
        valid_objs = [ImportedRow(r) for r in res["valid_records"]]
        return valid_objs, errors

    def import_records(self, valid_rows: List[Any], conflict_mode: str = "add_new_only", user_id: int = 1):
        """Imports validated rows into database."""
        if hasattr(self, "_last_parsed_file") and self._last_parsed_file:
            return self.validate_and_import(self._last_parsed_file, mode=conflict_mode, commit=True, user_id=user_id)
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=TEMPLATE_COLUMNS)
            writer.writeheader()
            for r in valid_rows:
                d = r if isinstance(r, dict) else r.__dict__
                row_dict = {
                    "category": d.get("category", ""),
                    "subcategory": d.get("subcategory", ""),
                    "product_name": d.get("product_name", ""),
                    "product_name_urdu": d.get("product_name_urdu", ""),
                    "sku": d.get("sku", ""),
                    "barcode": d.get("barcode", ""),
                    "unit": d.get("unit_code", d.get("unit", "")),
                    "size": d.get("size", ""),
                    "color": d.get("color", ""),
                    "design": d.get("design", ""),
                    "fabric_type": d.get("fabric_type", ""),
                    "dimensions": d.get("dimensions", ""),
                    "purchase_price": str(d.get("purchase_price", "0")),
                    "selling_price": str(d.get("selling_price", "0")),
                    "opening_stock": str(d.get("opening_stock", "0")),
                    "min_stock_alert": str(d.get("min_stock_alert", "5"))
                }
                writer.writerow(row_dict)
            tmp_path = f.name
        try:
            return self.validate_and_import(tmp_path, mode=conflict_mode, commit=True, user_id=user_id)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def validate_and_import(
        self,
        file_path: str,
        mode: str = "add_new_only",
        commit: bool = True,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """
        Validates and imports product records.
        Modes:
        - 'add_new_only': adds new SKUs; if SKU already exists, marks as duplicate error.
        - 'update_existing': updates price/stock/details if SKU exists, adds if new.
        - 'skip_existing': skips existing SKUs without error, adds new ones.

        Guarantees:
        - Never silently overwrites prices/stock unless 'update_existing' mode is explicitly selected.
        - Atomic transaction: entire import rolls back on fatal failure.
        - Reports row-level errors and warnings.
        """
        rows = self.parse_file(file_path)

        summary = {
            "total_rows": len(rows),
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "valid_records": []
        }

        if not rows:
            summary["errors"].append({"row": 0, "field": "file", "message": "File contains no data rows."})
            return summary

        cursor = self.conn.cursor()

        # Preload existing units
        cursor.execute("SELECT id, code, name FROM units;")
        db_units = cursor.fetchall()
        unit_code_to_id = {u["code"]: u["id"] for u in db_units}

        # Preload existing categories
        cursor.execute("SELECT id, code, name FROM categories;")
        cat_map = {c["name"].lower(): c["id"] for c in cursor.fetchall()}

        # Preload existing product SKUs
        cursor.execute("SELECT sku, id, product_id, cost_price, selling_price, stock_quantity FROM product_variants;")
        existing_variants = {v["sku"]: dict(v) for v in cursor.fetchall()}

        # Duplicate detection within the file itself
        seen_file_skus = set()

        validated_rows = []

        for row_idx, r in enumerate(rows, start=2):  # Row 2 is first data row in spreadsheet
            cat_name = r.get("category", "").strip()
            prod_name = r.get("product_name", "").strip()
            sku = r.get("sku", "").strip()
            unit_str = r.get("unit", "").strip().lower()

            row_errors = []

            # Required field validation
            if not cat_name:
                row_errors.append("Missing required field 'category'")
            if not prod_name:
                row_errors.append("Missing required field 'product_name'")
            if not sku:
                row_errors.append("Missing required field 'sku'")

            # Unit validation
            unit_code = SUPPORTED_UNITS_MAP.get(unit_str)
            if not unit_code:
                row_errors.append(f"Invalid unit '{r.get('unit')}'. Supported: Piece, Set, Pair, Meter, Yard/Gaz, Roll, Pack, Kg, Gram")

            # Duplicate check in file
            if sku:
                if sku in seen_file_skus:
                    row_errors.append(f"Duplicate SKU '{sku}' found multiple times within the import file")
                seen_file_skus.add(sku)

            # Price & Stock number validation
            purchase_price = Decimal("0.00")
            selling_price = Decimal("0.00")
            opening_stock = Decimal("0.000")
            min_stock = Decimal("5.000")

            if r.get("purchase_price"):
                try:
                    purchase_price = to_decimal(r["purchase_price"])
                    if purchase_price < 0:
                        row_errors.append("purchase_price cannot be negative")
                except Exception:
                    row_errors.append(f"Invalid purchase_price format: '{r['purchase_price']}'")

            if r.get("selling_price"):
                try:
                    selling_price = to_decimal(r["selling_price"])
                    if selling_price < 0:
                        row_errors.append("selling_price cannot be negative")
                except Exception:
                    row_errors.append(f"Invalid selling_price format: '{r['selling_price']}'")

            if r.get("opening_stock"):
                try:
                    opening_stock = to_qty_decimal(r["opening_stock"])
                    if opening_stock < 0:
                        row_errors.append("opening_stock cannot be negative")
                except Exception:
                    row_errors.append(f"Invalid opening_stock format: '{r['opening_stock']}'")

            if r.get("min_stock_alert"):
                try:
                    min_stock = to_qty_decimal(r["min_stock_alert"])
                except Exception:
                    pass

            # Existing in DB check
            exists_in_db = sku in existing_variants
            if exists_in_db:
                if mode == "add_new_only":
                    row_errors.append(f"SKU '{sku}' already exists in database (mode is 'Add New Only')")
                elif mode == "skip_existing":
                    summary["skipped"] += 1
                    continue

            if row_errors:
                summary["failed"] += 1
                for err in row_errors:
                    summary["errors"].append({"row": row_idx, "sku": sku, "message": err})
            else:
                validated_rows.append({
                    "row_idx": row_idx,
                    "category": cat_name,
                    "subcategory": r.get("subcategory", "").strip(),
                    "product_name": prod_name,
                    "product_name_urdu": r.get("product_name_urdu", "").strip(),
                    "sku": sku,
                    "barcode": r.get("barcode", "").strip() or sku,
                    "unit_code": unit_code,
                    "size": r.get("size", "").strip() or "Standard",
                    "color": r.get("color", "").strip() or "Standard",
                    "design": r.get("design", "").strip() or "Standard",
                    "fabric_type": r.get("fabric_type", "").strip() or "Standard",
                    "dimensions": r.get("dimensions", "").strip(),
                    "purchase_price": purchase_price,
                    "selling_price": selling_price,
                    "opening_stock": opening_stock,
                    "min_stock_alert": min_stock,
                    "exists_in_db": exists_in_db,
                    "existing_variant_id": existing_variants[sku]["id"] if exists_in_db else None,
                    "existing_product_id": existing_variants[sku]["product_id"] if exists_in_db else None
                })

        summary["valid_records"] = validated_rows

        # If not committing (preview mode) or if there are fatal errors that stop the batch
        if not commit or summary["failed"] > 0:
            return summary

        # ATOMIC DATABASE TRANSACTION
        try:
            self.conn.execute("BEGIN TRANSACTION;")

            for row in validated_rows:
                u_id = unit_code_to_id.get(row["unit_code"], 1)
                is_fabric = 1 if row["unit_code"] in ("MTR", "YD", "ROLL") else 0

                # 1. Resolve or Create Category
                cat_key = row["category"].lower()
                if cat_key in cat_map:
                    cat_id = cat_map[cat_key]
                else:
                    cat_code = f"CAT-{len(cat_map) + 1:03d}"
                    cursor.execute("""
                        INSERT INTO categories (code, name, is_active)
                        VALUES (?, ?, 1);
                    """, (cat_code, row["category"]))
                    cat_id = cursor.lastrowid
                    cat_map[cat_key] = cat_id

                # 2. Add or Update
                if row["exists_in_db"] and mode == "update_existing":
                    # Update variant details & pricing
                    cursor.execute("""
                        UPDATE product_variants
                        SET barcode = ?, size = ?, color = ?, design = ?, fabric_type = ?, dimensions = ?,
                            cost_price = ?, selling_price = ?, stock_quantity = ?
                        WHERE id = ?;
                    """, (
                        row["barcode"], row["size"], row["color"], row["design"], row["fabric_type"], row["dimensions"],
                        float(row["purchase_price"]), float(row["selling_price"]), float(row["opening_stock"]),
                        row["existing_variant_id"]
                    ))

                    # Update product name/unit
                    cursor.execute("""
                        UPDATE products
                        SET name = ?, name_urdu = ?, unit_id = ?, is_fabric = ?, min_stock_alert = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?;
                    """, (
                        row["product_name"], row["product_name_urdu"], u_id, is_fabric, float(row["min_stock_alert"]),
                        row["existing_product_id"]
                    ))
                    summary["updated"] += 1

                else:
                    # Insert Product
                    prod_code = f"PRD-{row['sku']}"
                    cursor.execute("""
                        INSERT INTO products (
                            category_id, code, barcode, name, name_urdu, unit_id, is_template, is_fabric,
                            min_stock_alert, base_cost_price, base_selling_price, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 1);
                    """, (
                        cat_id, prod_code, row["barcode"], row["product_name"], row["product_name_urdu"],
                        u_id, is_fabric, float(row["min_stock_alert"]), float(row["purchase_price"]), float(row["selling_price"])
                    ))
                    prod_id = cursor.lastrowid

                    # Insert Variant
                    cursor.execute("""
                        INSERT INTO product_variants (
                            product_id, sku, barcode, size, color, design, fabric_type, dimensions,
                            cost_price, selling_price, stock_quantity, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
                    """, (
                        prod_id, row["sku"], row["barcode"], row["size"], row["color"], row["design"],
                        row["fabric_type"], row["dimensions"], float(row["purchase_price"]), float(row["selling_price"]),
                        float(row["opening_stock"])
                    ))
                    var_id = cursor.lastrowid

                    # Record opening stock transaction if stock > 0
                    if row["opening_stock"] > Decimal("0.000"):
                        cursor.execute("""
                            INSERT INTO stock_transactions (
                                product_id, variant_id, transaction_type, quantity, unit_cost, notes, user_id
                            ) VALUES (?, ?, 'opening_stock', ?, ?, 'Bulk Excel/CSV Import', ?);
                        """, (prod_id, var_id, float(row["opening_stock"]), float(row["purchase_price"]), user_id))

                    summary["added"] += 1

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Database error during bulk import, all changes rolled back: {str(e)}")

        return summary

    def export_catalog_to_csv(self, file_path: str):
        """Exports complete active product catalog with variants, stock, and pricing to CSV."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.name as category, sc.name as subcategory, p.name as product_name, p.name_urdu,
                   v.sku, v.barcode, u.name as unit, v.size, v.color, v.design, v.fabric_type,
                   v.dimensions, v.cost_price, v.selling_price, v.stock_quantity, p.min_stock_alert
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN units u ON p.unit_id = u.id
            LEFT JOIN subcategories sc ON p.subcategory_id = sc.id
            WHERE p.is_active = 1 AND v.is_active = 1
            ORDER BY c.name ASC, p.name ASC, v.id ASC;
        """)
        rows = cursor.fetchall()

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TEMPLATE_COLUMNS)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    "category": r["category"],
                    "subcategory": r["subcategory"] or "",
                    "product_name": r["product_name"],
                    "product_name_urdu": r["name_urdu"] or "",
                    "sku": r["sku"],
                    "barcode": r["barcode"] or r["sku"],
                    "unit": r["unit"],
                    "size": r["size"] or "",
                    "color": r["color"] or "",
                    "design": r["design"] or "",
                    "fabric_type": r["fabric_type"] or "",
                    "dimensions": r["dimensions"] or "",
                    "purchase_price": f"{r['cost_price']:.2f}",
                    "selling_price": f"{r['selling_price']:.2f}",
                    "opening_stock": f"{r['stock_quantity']:g}",
                    "min_stock_alert": f"{r['min_stock_alert']:g}"
                })

        return len(rows)

    def export_sales_to_csv(self, file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """Exports sales transactions and invoices to CSV with UTF-8 BOM."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        cursor = self.conn.cursor()
        query = """
            SELECT s.invoice_number, s.sale_date, COALESCE(c.name, 'Walk-in Customer') as customer_name,
                   COALESCE(c.phone, '') as customer_phone, s.subtotal, s.discount_amount, s.tax_amount,
                   s.grand_total, s.paid_amount, s.balance_amount, s.payment_status, s.payment_method,
                   u.full_name as cashier_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN users u ON s.cashier_id = u.id
            WHERE 1=1
        """
        params = []
        if start_date:
            query += " AND DATE(s.sale_date) >= DATE(?)"
            params.append(start_date)
        if end_date:
            query += " AND DATE(s.sale_date) <= DATE(?)"
            params.append(end_date)
        query += " ORDER BY s.id DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        fieldnames = [
            "invoice_number", "sale_date", "customer_name", "customer_phone", "cashier_name",
            "subtotal", "discount_amount", "tax_amount", "grand_total", "paid_amount",
            "balance_amount", "payment_status", "payment_method"
        ]

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    "invoice_number": r["invoice_number"],
                    "sale_date": str(r["sale_date"]),
                    "customer_name": r["customer_name"],
                    "customer_phone": r["customer_phone"],
                    "cashier_name": r["cashier_name"] or "",
                    "subtotal": f"{r['subtotal']:.2f}",
                    "discount_amount": f"{r['discount_amount']:.2f}",
                    "tax_amount": f"{r['tax_amount']:.2f}",
                    "grand_total": f"{r['grand_total']:.2f}",
                    "paid_amount": f"{r['paid_amount']:.2f}",
                    "balance_amount": f"{r['balance_amount']:.2f}",
                    "payment_status": r["payment_status"],
                    "payment_method": r["payment_method"]
                })

        return len(rows)

    def export_customers_to_csv(self, file_path: str) -> int:
        """Exports customer directory, credit limits, and balances to CSV."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT code, name, phone, address, city, credit_limit, opening_balance, current_balance, discount_percent, notes
            FROM customers
            WHERE is_active = 1
            ORDER BY name ASC;
        """)
        rows = cursor.fetchall()

        fieldnames = ["code", "name", "phone", "address", "city", "credit_limit", "opening_balance", "current_balance", "discount_percent", "notes"]

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    "code": r["code"],
                    "name": r["name"],
                    "phone": r["phone"] or "",
                    "address": r["address"] or "",
                    "city": r["city"] or "Local",
                    "credit_limit": f"{r['credit_limit']:.2f}",
                    "opening_balance": f"{r['opening_balance']:.2f}",
                    "current_balance": f"{r['current_balance']:.2f}",
                    "discount_percent": f"{r['discount_percent']:.2f}",
                    "notes": r["notes"] or ""
                })

        return len(rows)

    def export_suppliers_to_csv(self, file_path: str) -> int:
        """Exports supplier registry and payable balances to CSV."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT code, company_name, contact_person, phone, address, opening_balance, current_balance, notes
            FROM suppliers
            WHERE is_active = 1
            ORDER BY company_name ASC;
        """)
        rows = cursor.fetchall()

        fieldnames = ["code", "company_name", "contact_person", "phone", "address", "opening_balance", "current_balance", "notes"]

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    "code": r["code"],
                    "company_name": r["company_name"],
                    "contact_person": r["contact_person"] or "",
                    "phone": r["phone"] or "",
                    "address": r["address"] or "",
                    "opening_balance": f"{r['opening_balance']:.2f}",
                    "current_balance": f"{r['current_balance']:.2f}",
                    "notes": r["notes"] or ""
                })

        return len(rows)

    def export_catalog_to_excel(self, file_path: str) -> int:
        """Exports product catalog to Excel (.xlsx) using openpyxl with fallback to CSV."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Arooj Catalog"

            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT c.name as category, sc.name as subcategory, p.name as product_name,
                       p.name_urdu, v.sku, v.barcode, u.name as unit, v.size, v.color,
                       v.design, v.fabric_type, v.dimensions, v.cost_price, v.selling_price,
                       v.stock_quantity, p.min_stock_alert
                FROM product_variants v
                JOIN products p ON v.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                LEFT JOIN subcategories sc ON p.subcategory_id = sc.id
                JOIN units u ON p.unit_id = u.id
                WHERE p.is_active = 1 AND v.is_active = 1
                ORDER BY c.name, p.name, v.sku;
            """)
            rows = cursor.fetchall()

            ws.append(TEMPLATE_COLUMNS)
            header_fill = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid")
            header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            for col_idx in range(1, len(TEMPLATE_COLUMNS) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            for r in rows:
                ws.append([
                    r["category"], r["subcategory"] or "", r["product_name"], r["name_urdu"] or "",
                    r["sku"], r["barcode"] or r["sku"], r["unit"], r["size"] or "",
                    r["color"] or "", r["design"] or "", r["fabric_type"] or "", r["dimensions"] or "",
                    float(r["cost_price"]), float(r["selling_price"]),
                    float(r["stock_quantity"]), float(r["min_stock_alert"])
                ])

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            wb.save(file_path)
            return len(rows)
        except ImportError:
            csv_path = str(Path(file_path).with_suffix(".csv"))
            return self.export_catalog_to_csv(csv_path)

    def export_sales_to_excel(self, file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """Exports sales to Excel (.xlsx) using openpyxl with fallback to CSV."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sales Invoices"

            headers = [
                "Invoice Number", "Sale Date", "Customer Name", "Customer Phone", "Cashier",
                "Subtotal (Rs.)", "Discount (Rs.)", "Tax (Rs.)", "Grand Total (Rs.)",
                "Paid (Rs.)", "Balance (Rs.)", "Status", "Payment Method"
            ]
            ws.append(headers)

            cursor = self.conn.cursor()
            query = """
                SELECT s.invoice_number, s.sale_date, COALESCE(c.name, 'Walk-in Customer') as customer_name,
                       COALESCE(c.phone, '') as customer_phone, s.subtotal, s.discount_amount, s.tax_amount,
                       s.grand_total, s.paid_amount, s.balance_amount, s.payment_status, s.payment_method,
                       u.full_name as cashier_name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN users u ON s.cashier_id = u.id
                WHERE 1=1
            """
            params = []
            if start_date:
                query += " AND DATE(s.sale_date) >= DATE(?)"
                params.append(start_date)
            if end_date:
                query += " AND DATE(s.sale_date) <= DATE(?)"
                params.append(end_date)
            query += " ORDER BY s.id DESC;"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for r in rows:
                ws.append([
                    r["invoice_number"], str(r["sale_date"]), r["customer_name"], r["customer_phone"],
                    r["cashier_name"] or "", float(r["subtotal"]), float(r["discount_amount"]),
                    float(r["tax_amount"]), float(r["grand_total"]), float(r["paid_amount"]),
                    float(r["balance_amount"]), r["payment_status"], r["payment_method"]
                ])

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            wb.save(file_path)
            return len(rows)
        except ImportError:
            csv_path = str(Path(file_path).with_suffix(".csv"))
            return self.export_sales_to_csv(csv_path, start_date, end_date)

