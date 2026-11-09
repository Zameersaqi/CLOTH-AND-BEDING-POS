"""
Sales Reports, Invoices & Receipt Reprinting Screen for Arooj POS
Includes invoice editing with manager authorization, inventory & balance reconciliation,
and audit trail inspection.
"""

from decimal import Decimal
from typing import Optional, List
from app.config import format_currency, to_decimal, to_qty_decimal
from app.services.printer_service import PrinterService
from app.ui.pos_screen import ReceiptDialog

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QHeaderView, QMessageBox, QDateEdit, QDialog,
        QFormLayout, QGroupBox
    )
    from PySide6.QtCore import Qt, QDate
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object
    QDialog = object

if PYSIDE_AVAILABLE:
    class AuditLogsDialog(QDialog):
        """Displays historical audit log trail for a specific invoice."""
        def __init__(self, invoice_number: str, logs: list, parent=None):
            super().__init__(parent)
            self.setWindowTitle(f"Audit Trail - Invoice {invoice_number}")
            self.setMinimumSize(680, 380)
            layout = QVBoxLayout(self)

            title = QLabel(f"Revision History for Invoice: {invoice_number}")
            title.setStyleSheet("font-size: 14px; font-weight: bold; color: #064e3b;")
            layout.addWidget(title)

            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Date & Time", "Old Grand Total", "New Grand Total", "Edited By", "Changes & Reason"])
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

            table.setRowCount(len(logs))
            for i, l in enumerate(logs):
                table.setItem(i, 0, QTableWidgetItem(str(l.get("created_at", ""))))
                table.setItem(i, 1, QTableWidgetItem(format_currency(l.get("old_grand_total", 0))))
                table.setItem(i, 2, QTableWidgetItem(format_currency(l.get("new_grand_total", 0))))
                table.setItem(i, 3, QTableWidgetItem(str(l.get("edited_by", "Manager"))))
                table.setItem(i, 4, QTableWidgetItem(str(l.get("changes_summary", ""))))
            layout.addWidget(table)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)

    class EditInvoiceDialog(QDialog):
        """Allows authorized editing of product quantities, prices, discount and customer for an existing invoice."""
        def __init__(self, sale_data: dict, sales_repo, settings_repo, parent=None):
            super().__init__(parent)
            self.sale_data = sale_data
            self.sales_repo = sales_repo
            self.settings_repo = settings_repo
            self.invoice_number = sale_data["invoice_number"]
            self.revised_sale_data = None

            self.setWindowTitle(f"Edit Invoice #{self.invoice_number} - Controlled Revision")
            self.setMinimumSize(720, 580)
            layout = QVBoxLayout(self)
            layout.setSpacing(10)

            # Header info
            info_box = QHBoxLayout()
            cust_name = sale_data.get("customer_name") or "Walk-in Customer"
            info_lbl = QLabel(f"<b>Invoice:</b> {self.invoice_number} | <b>Date:</b> {sale_data.get('sale_date', '')} | <b>Customer:</b> {cust_name}")
            info_box.addWidget(info_lbl)
            info_box.addStretch()

            if sale_data.get("is_revised"):
                rev_badge = QLabel(f"Revised (v{sale_data.get('revision_count', 0) + 1})")
                rev_badge.setStyleSheet("background-color: #fef3c7; color: #b45309; padding: 3px 8px; font-weight: bold; border-radius: 4px;")
                info_box.addWidget(rev_badge)

            layout.addLayout(info_box)

            # Items table
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Product / Item", "Variant", "Quantity", "Unit Price (Rs.)", "Line Total (Rs.)"])
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            layout.addWidget(self.table)

            self.qty_editors = []
            self.price_editors = []
            self.line_total_labels = []

            items = sale_data.get("items", [])
            self.table.setRowCount(len(items))
            for i, it in enumerate(items):
                p_item = QTableWidgetItem(it.get("product_name", ""))
                p_item.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(i, 0, p_item)

                v_str = it.get("variant_title") or f"{it.get('size', '')} {it.get('color', '')}".strip() or "Standard"
                v_item = QTableWidgetItem(v_str)
                v_item.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(i, 1, v_item)

                # Quantity editor
                qty_val = float(it.get("quantity", 1))
                qty_edit = QLineEdit(f"{qty_val:g}")
                qty_edit.setAlignment(Qt.AlignCenter)
                qty_edit.setFixedWidth(80)
                qty_edit.textChanged.connect(self.recalculate_totals)
                self.table.setCellWidget(i, 2, qty_edit)
                self.qty_editors.append((it, qty_edit))

                # Price editor
                price_val = float(it.get("transaction_price", it.get("unit_price", 0)))
                price_edit = QLineEdit(f"{price_val:.2f}")
                price_edit.setAlignment(Qt.AlignRight)
                price_edit.setFixedWidth(100)
                price_edit.textChanged.connect(self.recalculate_totals)
                self.table.setCellWidget(i, 3, price_edit)
                self.price_editors.append(price_edit)

                tot_lbl = QLabel(f"Rs. {float(it.get('line_total', 0)):,.2f}")
                tot_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                tot_lbl.setStyleSheet("font-weight: bold;")
                self.table.setCellWidget(i, 4, tot_lbl)
                self.line_total_labels.append(tot_lbl)

            # Totals & Discount controls
            totals_frame = QGroupBox("Invoice Revision Summary")
            t_layout = QFormLayout(totals_frame)

            self.subtotal_lbl = QLabel(format_currency(sale_data.get("subtotal", 0)))
            self.subtotal_lbl.setStyleSheet("font-weight: bold;")
            t_layout.addRow("Revised Subtotal:", self.subtotal_lbl)

            self.discount_edit = QLineEdit(f"{float(sale_data.get('discount_amount', 0)):.2f}")
            self.discount_edit.setFixedWidth(120)
            self.discount_edit.textChanged.connect(self.recalculate_totals)
            t_layout.addRow("Bill Discount (Rs.):", self.discount_edit)

            self.grand_total_lbl = QLabel(format_currency(sale_data.get("grand_total", 0)))
            self.grand_total_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #047857;")
            t_layout.addRow("Revised Grand Total:", self.grand_total_lbl)

            self.diff_lbl = QLabel("Rs. 0.00 (No change)")
            self.diff_lbl.setStyleSheet("font-weight: bold; color: #64748b;")
            t_layout.addRow("Variance from Original:", self.diff_lbl)

            layout.addWidget(totals_frame)

            # Authorization & Reason form
            auth_frame = QGroupBox("Manager Authorization & Audit Reason")
            a_layout = QFormLayout(auth_frame)

            self.reason_edit = QLineEdit()
            self.reason_edit.setPlaceholderText("E.g., Customer negotiated counter discount / corrected item length")
            self.reason_edit.setText("Invoice correction requested at counter")
            a_layout.addRow("Reason for Edit:", self.reason_edit)

            self.pin_edit = QLineEdit()
            self.pin_edit.setEchoMode(QLineEdit.Password)
            self.pin_edit.setPlaceholderText("Enter Manager PIN...")
            self.pin_edit.setFixedWidth(140)
            a_layout.addRow("Manager PIN:", self.pin_edit)

            layout.addWidget(auth_frame)

            # Actions
            btn_box = QHBoxLayout()

            history_btn = QPushButton("📜 View Revision Logs")
            history_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px;")
            history_btn.clicked.connect(self.on_view_logs)
            btn_box.addWidget(history_btn)

            btn_box.addStretch()

            save_btn = QPushButton("💾 Save & Reconcile (Enter)")
            save_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 20px; font-size: 13px;")
            save_btn.setDefault(True)
            save_btn.clicked.connect(self.on_save)
            btn_box.addWidget(save_btn)

            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet("background-color: #f1f5f9; color: #334155; font-weight: bold; padding: 10px 16px; border: 1px solid #cbd5e1;")
            cancel_btn.clicked.connect(self.reject)
            btn_box.addWidget(cancel_btn)

            layout.addLayout(btn_box)

            self.recalculate_totals()

        def recalculate_totals(self):
            subtotal = Decimal("0.00")
            for idx, (it, q_edit) in enumerate(self.qty_editors):
                p_edit = self.price_editors[idx]
                try:
                    q = to_qty_decimal(q_edit.text().strip() or "0")
                except Exception:
                    q = Decimal("0.00")
                try:
                    p = to_decimal(p_edit.text().strip() or "0")
                except Exception:
                    p = Decimal("0.00")

                line_tot = to_decimal(q * p)
                subtotal += line_tot
                self.line_total_labels[idx].setText(f"Rs. {line_tot:,.2f}")

            try:
                disc = to_decimal(self.discount_edit.text().strip() or "0")
            except Exception:
                disc = Decimal("0.00")

            gt = max(Decimal("0.00"), subtotal - disc)
            orig_gt = to_decimal(self.sale_data.get("grand_total", 0))
            diff = gt - orig_gt

            self.subtotal_lbl.setText(format_currency(subtotal))
            self.grand_total_lbl.setText(format_currency(gt))

            if diff > Decimal("0.00"):
                self.diff_lbl.setText(f"+Rs. {diff:,.2f} (Receivable increased)")
                self.diff_lbl.setStyleSheet("font-weight: bold; color: #059669;")
            elif diff < Decimal("0.00"):
                self.diff_lbl.setText(f"-Rs. {abs(diff):,.2f} (Refund/Credit to customer)")
                self.diff_lbl.setStyleSheet("font-weight: bold; color: #dc2626;")
            else:
                self.diff_lbl.setText("Rs. 0.00 (No change)")
                self.diff_lbl.setStyleSheet("font-weight: bold; color: #64748b;")

        def on_view_logs(self):
            logs = self.sales_repo.get_invoice_audit_logs(self.invoice_number)
            if not logs:
                QMessageBox.information(self, "Audit Trail", f"No revision history found for Invoice {self.invoice_number}.")
                return
            dlg = AuditLogsDialog(self.invoice_number, logs, self)
            dlg.exec()

        def on_save(self):
            # Validate Manager PIN
            settings = self.settings_repo.get_all_settings()
            correct_pin = settings.get("manager_pin", "1234")
            entered_pin = self.pin_edit.text().strip()
            if entered_pin != correct_pin:
                QMessageBox.critical(self, "Access Denied", "Invalid Manager PIN.\nInvoice editing requires verified Manager authorization.")
                self.pin_edit.selectAll()
                self.pin_edit.setFocus()
                return

            reason = self.reason_edit.text().strip()
            if not reason:
                QMessageBox.warning(self, "Reason Required", "Please provide a brief reason for revising this invoice.")
                self.reason_edit.setFocus()
                return

            # Build updated_items payload
            updated_items = []
            for idx, (it, q_edit) in enumerate(self.qty_editors):
                p_edit = self.price_editors[idx]
                try:
                    q = to_qty_decimal(q_edit.text().strip())
                    p = to_decimal(p_edit.text().strip())
                except Exception as e:
                    QMessageBox.warning(self, "Input Error", f"Invalid quantity or price for {it['product_name']}: {e}")
                    return

                if q <= Decimal("0"):
                    QMessageBox.warning(self, "Invalid Quantity", f"Quantity for {it['product_name']} must be greater than zero.")
                    return

                updated_items.append({
                    "item_id": it["id"],
                    "quantity": q,
                    "transaction_price": p
                })

            disc = to_decimal(self.discount_edit.text().strip() or "0")

            confirm = QMessageBox.question(
                self,
                "Confirm Invoice Revision",
                f"Apply revisions to Invoice {self.invoice_number}?\n\n"
                f"• Inventory stock will be adjusted for quantity differences.\n"
                f"• Customer accounts/ledgers will be reconciled.\n"
                f"• A permanent audit record will be logged.\n\nProceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return

            success, msg = self.sales_repo.update_invoice(
                invoice_number=self.invoice_number,
                updated_items=updated_items,
                new_discount=disc,
                reason=reason,
                editor_name="Manager",
                manager_pin_verified=True
            )

            if success:
                QMessageBox.information(self, "Invoice Updated", f"Invoice {self.invoice_number} revised successfully!\n{msg}")
                self.revised_sale_data = self.sales_repo.get_sale_by_invoice(self.invoice_number)
                self.accept()
            else:
                QMessageBox.critical(self, "Update Failed", msg)

    class ReportsScreen(QWidget):
        def __init__(self, sales_repo, settings_repo, parent=None):
            super().__init__(parent)
            self.sales_repo = sales_repo
            self.settings_repo = settings_repo
            self.init_ui()
            self.load_invoices()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            top_box = QHBoxLayout()
            title = QLabel("Sales Invoices & Reports (سیلز انوائس رپورٹ)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            top_box.addWidget(title)
            top_box.addStretch()

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search invoice number or customer...")
            self.search_input.setFixedWidth(240)
            self.search_input.textChanged.connect(self.load_invoices)
            top_box.addWidget(self.search_input)

            layout.addLayout(top_box)

            # Invoices Table
            self.table = QTableWidget()
            self.table.setColumnCount(8)
            self.table.setHorizontalHeaderLabels([
                "Invoice #", "Date & Time", "Customer", "Payment", "Subtotal", "Discount", "Grand Total", "Status"
            ])
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            layout.addWidget(self.table)

            # Action bar
            btn_box = QHBoxLayout()

            reprint_btn = QPushButton("Reprint Receipt (F12)")
            reprint_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 18px;")
            reprint_btn.clicked.connect(self.on_reprint)

            edit_btn = QPushButton("✏️ Edit Selected Invoice")
            edit_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px 18px;")
            edit_btn.clicked.connect(self.on_edit_invoice)

            audit_btn = QPushButton("📜 View Audit Trail")
            audit_btn.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 10px 18px;")
            audit_btn.clicked.connect(self.on_view_audit_logs)

            return_btn = QPushButton("Process Return (واپسی)")
            return_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 10px 18px;")
            return_btn.clicked.connect(self.on_return)

            btn_box.addWidget(reprint_btn)
            btn_box.addWidget(edit_btn)
            btn_box.addWidget(audit_btn)
            btn_box.addWidget(return_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

        def load_invoices(self):
            cursor = self.sales_repo.conn.cursor()
            query = """
                SELECT s.id, s.invoice_number, s.sale_date, s.subtotal, s.discount_amount, s.grand_total,
                       s.paid_amount, s.balance_amount, s.payment_status, s.payment_method, s.is_returned,
                       s.is_revised, s.revision_count,
                       c.name as customer_name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE 1=1
            """
            search = self.search_input.text().strip()
            params = []
            if search:
                query += " AND (s.invoice_number LIKE ? OR c.name LIKE ?)"
                p = f"%{search}%"
                params.extend([p, p])
            query += " ORDER BY s.id DESC LIMIT 100;"
            cursor.execute(query, params)
            self.invoices = [dict(r) for r in cursor.fetchall()]

            self.table.setRowCount(len(self.invoices))
            for i, inv in enumerate(self.invoices):
                self.table.setItem(i, 0, QTableWidgetItem(inv["invoice_number"]))
                self.table.setItem(i, 1, QTableWidgetItem(str(inv["sale_date"])))
                self.table.setItem(i, 2, QTableWidgetItem(inv["customer_name"] or "Walk-in Customer"))
                self.table.setItem(i, 3, QTableWidgetItem(inv["payment_method"]))
                self.table.setItem(i, 4, QTableWidgetItem(format_currency(inv["subtotal"])))
                self.table.setItem(i, 5, QTableWidgetItem(format_currency(inv["discount_amount"])))
                self.table.setItem(i, 6, QTableWidgetItem(format_currency(inv["grand_total"])))

                status_parts = []
                if inv["is_returned"]:
                    status_parts.append("Returned")
                else:
                    status_parts.append(inv["payment_status"].capitalize())

                if inv.get("is_revised"):
                    rev_c = inv.get("revision_count", 0) + 1
                    status_parts.append(f"Rev v{rev_c}")

                status_str = " | ".join(status_parts)
                st_item = QTableWidgetItem(status_str)
                if inv["is_returned"]:
                    st_item.setForeground(Qt.red)
                elif inv.get("is_revised"):
                    st_item.setForeground(Qt.darkYellow)
                elif inv["payment_status"] == "paid":
                    st_item.setForeground(Qt.darkGreen)
                self.table.setItem(i, 7, st_item)

        def on_reprint(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.invoices):
                QMessageBox.information(self, "Select Invoice", "Please select an invoice from the table to reprint.")
                return
            inv = self.invoices[row]
            sale_data = self.sales_repo.get_sale_by_invoice(inv["invoice_number"])
            if sale_data:
                settings = self.settings_repo.get_all_settings()
                printer = PrinterService(paper_width=settings.get("receipt_paper_width", "80mm"))
                dlg = ReceiptDialog(sale_data, settings, printer, parent=self)
                dlg.exec()

        def on_edit_invoice(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.invoices):
                QMessageBox.information(self, "Select Invoice", "Please select an invoice from the table to edit.")
                return
            inv = self.invoices[row]
            if inv.get("is_returned"):
                QMessageBox.warning(self, "Invoice Returned", "Cannot edit an invoice that has already been returned.")
                return

            sale_data = self.sales_repo.get_sale_by_invoice(inv["invoice_number"])
            if not sale_data:
                QMessageBox.warning(self, "Not Found", f"Could not load data for invoice {inv['invoice_number']}.")
                return

            dlg = EditInvoiceDialog(sale_data, self.sales_repo, self.settings_repo, parent=self)
            if dlg.exec():
                self.load_invoices()
                if dlg.revised_sale_data:
                    ask_print = QMessageBox.question(
                        self, "Print Revised Receipt",
                        f"Invoice {inv['invoice_number']} updated successfully!\n\nWould you like to print or preview the revised thermal receipt now?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if ask_print == QMessageBox.Yes:
                        settings = self.settings_repo.get_all_settings()
                        printer = PrinterService(paper_width=settings.get("receipt_paper_width", "80mm"))
                        rdlg = ReceiptDialog(dlg.revised_sale_data, settings, printer, parent=self)
                        rdlg.exec()

        def on_view_audit_logs(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.invoices):
                QMessageBox.information(self, "Select Invoice", "Please select an invoice to view its revision logs.")
                return
            inv = self.invoices[row]
            logs = self.sales_repo.get_invoice_audit_logs(inv["invoice_number"])
            if not logs:
                QMessageBox.information(self, "Audit Trail", f"No revision history found for Invoice {inv['invoice_number']}.")
                return
            dlg = AuditLogsDialog(inv["invoice_number"], logs, self)
            dlg.exec()

        def on_return(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.invoices):
                QMessageBox.information(self, "Select Invoice", "Please select an invoice to process return.")
                return
            inv = self.invoices[row]
            if inv["is_returned"]:
                QMessageBox.warning(self, "Already Returned", "This invoice has already been returned.")
                return

            reply = QMessageBox.question(
                self, "Confirm Return",
                f"Process return for Invoice {inv['invoice_number']} for Rs. {inv['grand_total']:,.2f}?\nThis will restore product inventory and adjust accounts.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                sale_data = self.sales_repo.get_sale_by_invoice(inv["invoice_number"])
                ret_items = [(it["id"], Decimal(str(it["quantity"])), Decimal(str(it["transaction_price"]))) for it in sale_data["items"]]
                ret_code = self.sales_repo.record_return(inv["invoice_number"], ret_items, "Customer return at counter", 1)
                QMessageBox.information(self, "Return Processed", f"Return recorded: {ret_code}\nStock and ledgers adjusted.")
                self.load_invoices()
else:
    class ReportsScreen:
        pass
    class EditInvoiceDialog:
        pass
    class AuditLogsDialog:
        pass
