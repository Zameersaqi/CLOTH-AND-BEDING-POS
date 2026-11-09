"""
Supplier Repository for Suppliers, Purchases, and Supplier Ledger
"""

import sqlite3
from typing import List, Optional, Union, Dict, Any
from decimal import Decimal
from app.models.entities import Supplier
from app.config import to_decimal, to_qty_decimal

class SupplierRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_all(self, search: Optional[str] = None) -> List[Supplier]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM suppliers WHERE is_active = 1"
        params = []
        if search:
            query += " AND (company_name LIKE ? OR phone LIKE ? OR code LIKE ?)"
            s = f"%{search.strip()}%"
            params.extend([s, s, s])
        query += " ORDER BY company_name ASC;"
        cursor.execute(query, params)
        return [
            Supplier(
                id=r["id"],
                code=r["code"],
                company_name=r["company_name"],
                contact_person=r["contact_person"],
                phone=r["phone"],
                address=r["address"],
                opening_balance=to_decimal(r["opening_balance"]),
                current_balance=to_decimal(r["current_balance"]),
                notes=r["notes"],
                is_active=bool(r["is_active"])
            ) for r in cursor.fetchall()
        ]

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id = ?;", (supplier_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return Supplier(
            id=r["id"],
            code=r["code"],
            company_name=r["company_name"],
            contact_person=r["contact_person"],
            phone=r["phone"],
            address=r["address"],
            opening_balance=to_decimal(r["opening_balance"]),
            current_balance=to_decimal(r["current_balance"]),
            notes=r["notes"],
            is_active=bool(r["is_active"])
        )

    def create(self, supp: Union[Supplier, dict]) -> int:
        if isinstance(supp, dict):
            supp = Supplier(
                id=supp.get("id"),
                code=supp.get("code", ""),
                company_name=supp.get("company_name", ""),
                contact_person=supp.get("contact_person"),
                phone=supp.get("phone"),
                address=supp.get("address"),
                opening_balance=to_decimal(supp.get("opening_balance", "0.00")),
                current_balance=to_decimal(supp.get("current_balance", supp.get("opening_balance", "0.00"))),
                notes=supp.get("notes"),
                is_active=bool(supp.get("is_active", True))
            )

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO suppliers (code, company_name, contact_person, phone, address, opening_balance, current_balance, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            supp.code, supp.company_name, supp.contact_person, supp.phone, supp.address,
            float(supp.opening_balance), float(supp.current_balance), supp.notes
        ))
        supp_id = cursor.lastrowid
        if supp.opening_balance > Decimal("0.00"):
            cursor.execute("""
                INSERT INTO supplier_ledger (supplier_id, transaction_type, debit, credit, running_balance, description)
                VALUES (?, 'opening_balance', 0.0, ?, ?, 'Opening Payable Balance');
            """, (supp_id, float(supp.opening_balance), float(supp.opening_balance)))
        self.conn.commit()
        return supp_id

    def record_purchase(
        self,
        purchase_invoice_no: Union[str, dict],
        supplier_id: Optional[int] = None,
        subtotal: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        grand_total: Decimal = Decimal("0.00"),
        paid_amount: Decimal = Decimal("0.00"),
        items: Optional[List[dict]] = None,
        user_id: int = 1,
        **kwargs
    ) -> int:
        if isinstance(purchase_invoice_no, dict):
            d = purchase_invoice_no
            user_id = supplier_id if isinstance(supplier_id, int) and "supplier_id" in d else d.get("user_id", 1)
            supplier_id = d.get("supplier_id")
            subtotal = to_decimal(d.get("subtotal", d.get("total_amount", 0)))
            tax_amount = to_decimal(d.get("tax_amount", 0))
            grand_total = to_decimal(d.get("grand_total", d.get("net_amount", subtotal)))
            paid_amount = to_decimal(d.get("paid_amount", 0))
            raw_items = d.get("items", [])
            items = []
            for it in raw_items:
                items.append({
                    "product_id": it["product_id"],
                    "variant_id": it.get("variant_id"),
                    "quantity": to_qty_decimal(it["quantity"]),
                    "unit_price": to_decimal(it.get("unit_cost", it.get("unit_price", 0))),
                    "line_total": to_decimal(it.get("total_cost", it.get("line_total", 0)))
                })
            purchase_invoice_no = d.get("invoice_number", d.get("purchase_invoice_no", ""))

        if items is None:
            items = []

        cursor = self.conn.cursor()
        balance = grand_total - paid_amount
        status = "paid" if balance <= Decimal("0.00") else ("partial" if paid_amount > Decimal("0.00") else "unpaid")

        cursor.execute("""
            INSERT INTO purchases (
                purchase_invoice_no, supplier_id, purchase_date, subtotal, tax_amount, grand_total, paid_amount, balance_amount, payment_status
            ) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?);
        """, (purchase_invoice_no, supplier_id, float(subtotal), float(tax_amount), float(grand_total), float(paid_amount), float(balance), status))
        purchase_id = cursor.lastrowid

        # Update stock & record items
        for it in items:
            cursor.execute("""
                INSERT INTO purchase_items (purchase_id, product_id, variant_id, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (purchase_id, it["product_id"], it.get("variant_id"), float(it["quantity"]), float(it["unit_price"]), float(it["line_total"])))

            if it.get("variant_id"):
                cursor.execute("""
                    UPDATE product_variants
                    SET stock_quantity = stock_quantity + ?, cost_price = ?
                    WHERE id = ?;
                """, (float(it["quantity"]), float(it["unit_price"]), it["variant_id"]))

                cursor.execute("""
                    INSERT INTO stock_transactions (
                        product_id, variant_id, transaction_type, quantity, reference_id, reference_type, unit_cost, notes
                    ) VALUES (?, ?, 'purchase', ?, ?, 'purchase', ?, ?);
                """, (it["product_id"], it["variant_id"], float(it["quantity"]), purchase_id, float(it["unit_price"]), f"Purchased via {purchase_invoice_no}"))

        # Update supplier balance
        if balance > Decimal("0.00"):
            cursor.execute("UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?;", (float(balance), supplier_id))
            cursor.execute("SELECT current_balance FROM suppliers WHERE id = ?;", (supplier_id,))
            new_bal = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO supplier_ledger (supplier_id, purchase_id, transaction_type, debit, credit, running_balance, description)
                VALUES (?, ?, 'purchase_invoice', 0.0, ?, ?, ?);
            """, (supplier_id, purchase_id, float(grand_total), new_bal, f"Purchase {purchase_invoice_no}"))

        self.conn.commit()
        return purchase_id

    def pay_supplier(
        self,
        supplier_id: int,
        amount: Decimal,
        notes: str = "",
        payment_method: str = "cash",
        reference_no: Optional[str] = None,
        user_id: int = 1,
        **kwargs
    ) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?;", (float(amount), supplier_id))
        cursor.execute("SELECT current_balance FROM suppliers WHERE id = ?;", (supplier_id,))
        new_bal = cursor.fetchone()[0]
        desc = f"Paid supplier ({payment_method}): {notes}"
        if reference_no:
            desc += f" [Ref: {reference_no}]"
        cursor.execute("""
            INSERT INTO supplier_ledger (supplier_id, transaction_type, debit, credit, running_balance, description)
            VALUES (?, 'supplier_payment', ?, 0.0, ?, ?);
        """, (supplier_id, float(amount), new_bal, desc))
        self.conn.commit()
        return True

    record_payment = pay_supplier

    def update(self, supplier_id: int, code: str, company_name: str, contact_person: Optional[str], phone: Optional[str], address: Optional[str], notes: Optional[str]):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE suppliers
            SET code = ?, company_name = ?, contact_person = ?, phone = ?, address = ?, notes = ?
            WHERE id = ?;
        """, (code.strip(), company_name.strip(), contact_person, phone, address, notes, supplier_id))
        self.conn.commit()

    def deactivate(self, supplier_id: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE suppliers SET is_active = 0 WHERE id = ?;", (supplier_id,))
        self.conn.commit()

    def generate_unique_code(self, prefix: str = "SUP") -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM suppliers;")
        max_id = (cursor.fetchone()[0] or 0) + 1
        return f"{prefix}-{max_id:03d}"

    def get_purchases(self, supplier_id: Optional[int] = None, limit: int = 100) -> List[dict]:
        cursor = self.conn.cursor()
        query = """
            SELECT p.*, s.company_name as supplier_name, s.code as supplier_code
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
        """
        params = []
        if supplier_id:
            query += " AND p.supplier_id = ?"
            params.append(supplier_id)
        query += " ORDER BY p.id DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["subtotal"] = to_decimal(d["subtotal"])
            d["tax_amount"] = to_decimal(d["tax_amount"])
            d["grand_total"] = to_decimal(d["grand_total"])
            d["paid_amount"] = to_decimal(d["paid_amount"])
            d["balance_amount"] = to_decimal(d["balance_amount"])
            result.append(d)
        return result

    def get_supplier_ledger(self, supplier_id: int) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, created_at, transaction_type, debit, credit, running_balance, description
            FROM supplier_ledger
            WHERE supplier_id = ?
            ORDER BY id ASC;
        """, (supplier_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["debit"] = to_decimal(d["debit"])
            d["credit"] = to_decimal(d["credit"])
            d["running_balance"] = to_decimal(d["running_balance"])
            result.append(d)
        return result

