"""
Sales Repository for Invoicing, Transactions, Cart Persistence, and Receipts
"""

import sqlite3
import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from app.models.entities import Sale, CartItem
from app.config import to_decimal, to_qty_decimal

class SalesRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def generate_next_invoice_number(self) -> str:
        """Generates a sequential, date-stamped unique invoice number: INV-YYYYMMDD-XXXX."""
        today_str = datetime.date.today().strftime("%Y%m%d")
        prefix = f"INV-{today_str}-"
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT invoice_number FROM sales
            WHERE invoice_number LIKE ?
            ORDER BY id DESC LIMIT 1;
        """, (f"{prefix}%",))
        row = cursor.fetchone()
        if row:
            last_num_str = row[0].split("-")[-1]
            try:
                seq = int(last_num_str) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def record_sale(self, sale: Sale, tendered_cash: Decimal = Decimal("0.00"), change_due: Decimal = Decimal("0.00")) -> int:
        """
        Atomically records a complete sale:
        1. Inserts into sales header
        2. Inserts all sale_items (preserves original vs transaction prices)
        3. Inserts payment details
        4. Updates variant stock & records stock transactions
        5. If customer credit balance exists, updates customer ledger
        """
        cursor = self.conn.cursor()

        # 1. Insert Sales Header
        cursor.execute("""
            INSERT INTO sales (
                invoice_number, customer_id, cashier_id, sale_date, subtotal,
                discount_amount, discount_percent, tax_amount, grand_total,
                paid_amount, balance_amount, payment_status, payment_method, notes
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            sale.invoice_number,
            sale.customer_id,
            sale.cashier_id,
            float(sale.subtotal),
            float(sale.discount_amount),
            float(sale.discount_percent),
            float(sale.tax_amount),
            float(sale.grand_total),
            float(sale.paid_amount),
            float(sale.balance_amount),
            sale.payment_status,
            sale.payment_method,
            sale.notes
        ))
        sale_id = cursor.lastrowid

        # 2. Insert Sale Items and update inventory
        for item in sale.items:
            cursor.execute("""
                INSERT INTO sale_items (
                    sale_id, product_id, variant_id, roll_id, quantity, unit_name,
                    original_catalog_price, transaction_price, line_discount, line_total,
                    cost_price, is_price_overridden, override_reason, override_approved_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                sale_id,
                item.product_id,
                item.variant_id,
                item.roll_id,
                float(item.quantity),
                item.unit_name,
                float(item.original_catalog_price),
                float(item.transaction_price),
                float(item.line_discount),
                float(item.line_total),
                float(item.cost_price),
                1 if item.is_price_overridden else 0,
                item.override_reason,
                item.override_approved_by
            ))

            # Deduct stock from variant
            if item.variant_id:
                cursor.execute("""
                    UPDATE product_variants
                    SET stock_quantity = stock_quantity - ?
                    WHERE id = ?;
                """, (float(item.quantity), item.variant_id))

            # If tied to a specific fabric roll/thaan, deduct remaining length
            if item.roll_id:
                cursor.execute("""
                    UPDATE fabric_rolls
                    SET current_length = current_length - ?
                    WHERE id = ?;
                """, (float(item.quantity), item.roll_id))

            # Record stock movement transaction
            cursor.execute("""
                INSERT INTO stock_transactions (
                    product_id, variant_id, roll_id, transaction_type, quantity,
                    reference_id, reference_type, unit_cost, notes, user_id
                ) VALUES (?, ?, ?, 'sale', ?, ?, 'sales', ?, ?, ?);
            """, (
                item.product_id,
                item.variant_id,
                item.roll_id,
                -float(item.quantity),
                sale_id,
                float(item.cost_price),
                f"Sold in invoice {sale.invoice_number}",
                sale.cashier_id
            ))

        # 3. Insert Payment
        cursor.execute("""
            INSERT INTO sale_payments (
                sale_id, payment_method, amount, tendered_amount, change_returned, reference_note
            ) VALUES (?, ?, ?, ?, ?, ?);
        """, (
            sale_id,
            sale.payment_method,
            float(sale.paid_amount),
            float(tendered_cash),
            float(change_due),
            sale.notes
        ))

        # 4. Handle Customer Credit & Ledger
        if sale.customer_id and sale.balance_amount > Decimal("0.00"):
            # Update customer balance
            cursor.execute("""
                UPDATE customers
                SET current_balance = current_balance + ?
                WHERE id = ?;
            """, (float(sale.balance_amount), sale.customer_id))

            # Get new running balance
            cursor.execute("SELECT current_balance FROM customers WHERE id = ?;", (sale.customer_id,))
            new_bal = cursor.fetchone()[0]

            # Record in customer ledger
            cursor.execute("""
                INSERT INTO customer_ledger (
                    customer_id, sale_id, transaction_type, debit, credit, running_balance, description
                ) VALUES (?, ?, 'invoice', ?, 0.0, ?, ?);
            """, (
                sale.customer_id,
                sale_id,
                float(sale.grand_total),
                new_bal,
                f"Invoice {sale.invoice_number} (Unpaid: Rs. {sale.balance_amount})"
            ))

            if sale.paid_amount > Decimal("0.00"):
                cursor.execute("""
                    INSERT INTO customer_ledger (
                        customer_id, sale_id, transaction_type, debit, credit, running_balance, description
                    ) VALUES (?, ?, 'payment', 0.0, ?, ?, ?);
                """, (
                    sale.customer_id,
                    sale_id,
                    float(sale.paid_amount),
                    new_bal,
                    f"Cash payment at billing for {sale.invoice_number}"
                ))

        return sale_id

    def get_sale_by_invoice(self, invoice_number: str) -> Optional[dict]:
        """Fetches complete sale header, customer info, cashier name, and line items."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, c.name as customer_name, c.phone as customer_phone, u.full_name as cashier_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN users u ON s.cashier_id = u.id
            WHERE s.invoice_number = ?;
        """, (invoice_number,))
        s_row = cursor.fetchone()
        if not s_row:
            return None

        sale_dict = dict(s_row)
        sale_id = sale_dict["id"]

        # Fetch Items
        cursor.execute("""
            SELECT si.*, p.name as product_name, p.code as product_code,
                   v.size, v.color, v.design
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            LEFT JOIN product_variants v ON si.variant_id = v.id
            WHERE si.sale_id = ?;
        """, (sale_id,))
        sale_dict["items"] = [dict(r) for r in cursor.fetchall()]

        # Fetch Payments
        cursor.execute("SELECT * FROM sale_payments WHERE sale_id = ?;", (sale_id,))
        sale_dict["payments"] = [dict(r) for r in cursor.fetchall()]

        return sale_dict

    def hold_sale(self, hold_code: str, customer_id: Optional[int], cart_json: str, note: str, cashier_id: Optional[int]):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO held_sales (hold_code, customer_id, cart_payload_json, hold_note, cashier_id)
            VALUES (?, ?, ?, ?, ?);
        """, (hold_code, customer_id, cart_json, note, cashier_id))
        self.conn.commit()

    def get_held_sales(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM held_sales ORDER BY created_at DESC;")
        return [dict(r) for r in cursor.fetchall()]

    def delete_held_sale(self, hold_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM held_sales WHERE id = ?;", (hold_id,))
        self.conn.commit()

    def record_return(self, original_invoice_no: str, return_items: List[Tuple[int, Decimal, Decimal]], return_reason: str, cashier_id: int) -> str:
        """
        Executes a controlled sales return:
        - Restores inventory
        - Creates a credit/refund entry
        - Updates customer balance if applicable
        """
        cursor = self.conn.cursor()
        orig = self.get_sale_by_invoice(original_invoice_no)
        if not orig:
            raise ValueError(f"Original invoice {original_invoice_no} not found")

        ret_inv_no = f"RET-{original_invoice_no}"
        total_refund = Decimal("0.00")

        for item_id, qty_returned, refund_price in return_items:
            line_ret_amount = to_decimal(qty_returned * refund_price)
            total_refund += line_ret_amount

            # Fetch variant id to restore stock
            cursor.execute("SELECT product_id, variant_id, roll_id FROM sale_items WHERE id = ?;", (item_id,))
            it = cursor.fetchone()
            if it:
                prod_id, var_id, r_id = it[0], it[1], it[2]
                if var_id:
                    cursor.execute("UPDATE product_variants SET stock_quantity = stock_quantity + ? WHERE id = ?;", (float(qty_returned), var_id))
                if r_id:
                    cursor.execute("UPDATE fabric_rolls SET current_length = current_length + ? WHERE id = ?;", (float(qty_returned), r_id))
                cursor.execute("""
                    INSERT INTO stock_transactions (
                        product_id, variant_id, roll_id, transaction_type, quantity, reference_id, reference_type, notes, user_id
                    ) VALUES (?, ?, ?, 'customer_return', ?, ?, 'sales_return', ?, ?);
                """, (prod_id, var_id, r_id, float(qty_returned), orig["id"], f"Returned from {original_invoice_no}: {return_reason}", cashier_id))

        # Mark original sale as returned
        cursor.execute("UPDATE sales SET is_returned = 1, notes = notes || ' [RETURNED]' WHERE id = ?;", (orig["id"],))

        # Adjust customer balance if credit sale
        if orig["customer_id"]:
            cursor.execute("UPDATE customers SET current_balance = current_balance - ? WHERE id = ?;", (float(total_refund), orig["customer_id"]))
            cursor.execute("SELECT current_balance FROM customers WHERE id = ?;", (orig["customer_id"],))
            new_bal = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO customer_ledger (customer_id, sale_id, transaction_type, debit, credit, running_balance, description)
                VALUES (?, ?, 'return', 0.0, ?, ?, ?);
            """, (orig["customer_id"], orig["id"], float(total_refund), new_bal, f"Return credit for {original_invoice_no}"))

        self.conn.commit()
        return ret_inv_no

    def update_invoice(
        self,
        invoice_number: str,
        updated_items: List[dict],
        new_discount: Decimal,
        new_customer_id: Optional[int] = None,
        reason: str = "Invoice corrections",
        editor_name: str = "Manager",
        manager_pin_verified: bool = True
    ) -> Tuple[bool, str]:
        """
        Safely edits an existing invoice with strict accounting and inventory reconciliation:
        - Compares old items vs revised items
        - Reconciles inventory: stock is restored if quantity decreased; stock deducted if quantity increased
        - Records compensatory stock transactions with audit notes
        - Recalculates subtotal, discount, and grand total
        - Reconciles customer ledger and balance for credit invoices
        - Records complete historical audit log in invoice_audit_logs table
        - Increments revision_count and sets is_revised = 1
        """
        cursor = self.conn.cursor()
        sale = self.get_sale_by_invoice(invoice_number)
        if not sale:
            return False, f"Invoice {invoice_number} not found"
        if sale.get("is_returned"):
            return False, "Cannot edit an invoice that has already been returned"

        old_items = {it["id"]: it for it in sale.get("items", [])}
        new_subtotal = Decimal("0.00")
        changes = []

        for upd in updated_items:
            item_id = upd["item_id"]
            if item_id not in old_items:
                continue
            old_it = old_items[item_id]
            new_qty = to_qty_decimal(upd.get("quantity", old_it["quantity"]))
            new_price = to_decimal(upd.get("transaction_price", old_it["transaction_price"]))
            old_qty = to_qty_decimal(old_it["quantity"])
            old_price = to_decimal(old_it["transaction_price"])

            line_total = to_decimal(new_qty * new_price)
            new_subtotal += line_total

            # Inventory reconciliation: positive diff means customer took less -> restore stock
            qty_diff = old_qty - new_qty
            if qty_diff != Decimal("0"):
                var_id = old_it.get("variant_id")
                roll_id = old_it.get("roll_id")
                prod_id = old_it["product_id"]

                if var_id:
                    cursor.execute("UPDATE product_variants SET stock_quantity = stock_quantity + ? WHERE id = ?;", (float(qty_diff), var_id))
                if roll_id:
                    cursor.execute("UPDATE fabric_rolls SET current_length = current_length + ? WHERE id = ?;", (float(qty_diff), roll_id))

                cursor.execute("""
                    INSERT INTO stock_transactions (
                        product_id, variant_id, roll_id, transaction_type, quantity,
                        reference_id, reference_type, notes, user_id
                    ) VALUES (?, ?, ?, 'adjustment', ?, ?, 'invoice_edit', ?, ?);
                """, (prod_id, var_id, roll_id, float(qty_diff), sale["id"], f"Correction on {invoice_number}: Qty {old_qty:g} -> {new_qty:g}", sale.get("cashier_id", 1)))

                changes.append(f"{old_it['product_name']}: Qty {old_qty:g}->{new_qty:g}")

            if new_price != old_price:
                changes.append(f"{old_it['product_name']}: Price Rs.{old_price:,.2f}->Rs.{new_price:,.2f}")

            # Update sale item record
            is_override = 1 if new_price != to_decimal(old_it["original_catalog_price"]) else 0
            cursor.execute("""
                UPDATE sale_items
                SET quantity = ?, transaction_price = ?, line_total = ?, is_price_overridden = ?
                WHERE id = ?;
            """, (float(new_qty), float(new_price), float(line_total), is_override, item_id))

        new_discount = to_decimal(new_discount)
        new_grand_total = max(Decimal("0.00"), new_subtotal - new_discount)
        old_grand_total = to_decimal(sale["grand_total"])
        delta_gt = new_grand_total - old_grand_total

        old_cust_id = sale.get("customer_id")
        target_cust_id = new_customer_id if new_customer_id is not None else old_cust_id

        # Reconcile customer ledger and balance for customer accounts
        if target_cust_id and delta_gt != Decimal("0.00"):
            cursor.execute("UPDATE customers SET current_balance = current_balance + ? WHERE id = ?;", (float(delta_gt), target_cust_id))
            cursor.execute("SELECT current_balance FROM customers WHERE id = ?;", (target_cust_id,))
            bal_row = cursor.fetchone()
            new_bal = bal_row[0] if bal_row else 0.0

            cursor.execute("""
                INSERT INTO customer_ledger (
                    customer_id, sale_id, transaction_type, debit, credit, running_balance, description
                ) VALUES (?, ?, 'adjustment', ?, 0.0, ?, ?);
            """, (target_cust_id, sale["id"], float(delta_gt), new_bal, f"Invoice {invoice_number} corrected from Rs.{old_grand_total:,.2f} to Rs.{new_grand_total:,.2f}"))

        # Update sales header record
        new_balance = max(Decimal("0.00"), to_decimal(sale["balance_amount"]) + delta_gt)
        cursor.execute("""
            UPDATE sales
            SET subtotal = ?, discount_amount = ?, grand_total = ?, balance_amount = ?,
                customer_id = ?, is_revised = 1, revision_count = revision_count + 1
            WHERE id = ?;
        """, (float(new_subtotal), float(new_discount), float(new_grand_total), float(new_balance), target_cust_id, sale["id"]))

        # Record in invoice_audit_logs
        summary_text = f"Reason: {reason}. " + ("; ".join(changes) if changes else "Totals adjusted")
        cursor.execute("""
            INSERT INTO invoice_audit_logs (
                invoice_number, sale_id, old_subtotal, new_subtotal, old_discount, new_discount,
                old_grand_total, new_grand_total, changes_summary, edited_by, manager_pin_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            invoice_number, sale["id"], float(sale["subtotal"]), float(new_subtotal),
            float(sale["discount_amount"]), float(new_discount), float(old_grand_total),
            float(new_grand_total), summary_text, editor_name, 1 if manager_pin_verified else 0
        ))

        self.conn.commit()
        return True, "Invoice updated, inventory reconciled, and audit log recorded successfully"

    def get_invoice_audit_logs(self, invoice_number: str) -> List[dict]:
        """Returns chronological list of revisions and corrections for an invoice."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM invoice_audit_logs
            WHERE invoice_number = ?
            ORDER BY id DESC;
        """, (invoice_number,))
        return [dict(r) for r in cursor.fetchall()]
