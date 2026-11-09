"""
Supplier Repository for Suppliers, Purchases, and Supplier Ledger
"""

import sqlite3
from typing import List, Optional
from decimal import Decimal
from app.models.entities import Supplier
from app.config import to_decimal

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

    def create(self, supp: Supplier) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO suppliers (code, company_name, contact_person, phone, address, opening_balance, current_balance, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            supp.code, supp.company_name, supp.contact_person, supp.phone, supp.address,
            float(supp.opening_balance), float(supp.opening_balance), supp.notes
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
        purchase_invoice_no: str,
        supplier_id: int,
        subtotal: Decimal,
        tax_amount: Decimal,
        grand_total: Decimal,
        paid_amount: Decimal,
        items: List[dict]
    ) -> int:
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

    def pay_supplier(self, supplier_id: int, amount: Decimal, notes: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?;", (float(amount), supplier_id))
        cursor.execute("SELECT current_balance FROM suppliers WHERE id = ?;", (supplier_id,))
        new_bal = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO supplier_ledger (supplier_id, transaction_type, debit, credit, running_balance, description)
            VALUES (?, 'supplier_payment', ?, 0.0, ?, ?);
        """, (supplier_id, float(amount), new_bal, f"Paid supplier: {notes}"))
        self.conn.commit()
