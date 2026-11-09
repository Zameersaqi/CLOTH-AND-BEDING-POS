"""
Dedicated Supplier & Purchasing Management Screen for Arooj POS
Phase 7:
- Complete Supplier Profiles (Mills, Wholesalers, Distributors)
- Opening & Current Payable Balances
- Multi-Item Purchase Bills with automatic stock incrementation
- Supplier Payments & Ledger Statements
- Stock Receiving & Supplier Ledgers
"""

import csv
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from app.config import format_currency, to_decimal, to_qty_decimal
from app.models.entities import Supplier

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QMessageBox, QDialog,
        QDoubleSpinBox, QFormLayout, QFileDialog, QFrame, QGroupBox, QTabWidget,
        QSplitter
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class SupplierDialog(QDialog):
        """Add or Edit a Supplier Profile."""
        def __init__(self, supplier_repo, supplier=None, parent=None):
            super().__init__(parent)
            self.supplier_repo = supplier_repo
            self.supplier = supplier
            self.is_edit = supplier is not None
            self.setWindowTitle("Edit Supplier (سپلائر ترمیم)" if self.is_edit else "Add New Supplier (نیا سپلائر شامل کریں)")
            self.resize(450, 420)
            self.init_ui()
            if self.is_edit:
                self.populate_data()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            code_box = QHBoxLayout()
            self.code_input = QLineEdit()
            auto_btn = QPushButton("Auto")
            auto_btn.clicked.connect(self.on_auto_code)
            code_box.addWidget(self.code_input)
            code_box.addWidget(auto_btn)
            form.addRow("Supplier Code*:", code_box)

            self.name_input = QLineEdit()
            self.name_input.setPlaceholderText("e.g. Gul Ahmed Textile Mills / Al-Karam Fabrics")
            form.addRow("Company / Mill Name*:", self.name_input)

            self.contact_input = QLineEdit()
            self.contact_input.setPlaceholderText("Representative or broker name")
            form.addRow("Contact Person:", self.contact_input)

            self.phone_input = QLineEdit()
            self.phone_input.setPlaceholderText("0300-1234567")
            form.addRow("Phone / Mobile*:", self.phone_input)

            self.addr_input = QLineEdit()
            self.addr_input.setPlaceholderText("Faisalabad Cloth Market, Karachi, etc.")
            form.addRow("City / Address:", self.addr_input)

            self.open_bal_spin = QDoubleSpinBox()
            self.open_bal_spin.setRange(0.0, 100000000.0)
            self.open_bal_spin.setValue(0.0)
            self.open_bal_spin.setEnabled(not self.is_edit)
            form.addRow("Opening Balance (Rs. Payable):", self.open_bal_spin)

            self.notes_input = QLineEdit()
            self.notes_input.setPlaceholderText("Credit terms, fabric types supplied, etc.")
            form.addRow("Notes:", self.notes_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)

            save = QPushButton("Save Supplier (محفوظ کریں)")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.on_save)

            btn_box.addWidget(cancel)
            btn_box.addStretch()
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

            if not self.is_edit:
                self.on_auto_code()

        def on_auto_code(self):
            code = self.supplier_repo.generate_unique_code("SUP")
            self.code_input.setText(code)

        def populate_data(self):
            s = self.supplier
            self.code_input.setText(s.code)
            self.name_input.setText(s.company_name)
            self.contact_input.setText(s.contact_person or "")
            self.phone_input.setText(s.phone or "")
            self.addr_input.setText(s.address or "")
            self.open_bal_spin.setValue(float(s.opening_balance))
            self.notes_input.setText(s.notes or "")

        def on_save(self):
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation", "Company / Mill Name is required.")
                return

            code = self.code_input.text().strip()
            if not code:
                QMessageBox.warning(self, "Validation", "Supplier Code is required.")
                return

            contact = self.contact_input.text().strip() or None
            phone = self.phone_input.text().strip() or None
            addr = self.addr_input.text().strip() or None
            notes = self.notes_input.text().strip() or None

            try:
                if self.is_edit:
                    self.supplier_repo.update(
                        supplier_id=self.supplier.id,
                        code=code,
                        company_name=name,
                        contact_person=contact,
                        phone=phone,
                        address=addr,
                        notes=notes
                    )
                else:
                    open_bal = to_decimal(self.open_bal_spin.value())
                    s = Supplier(
                        id=None,
                        code=code,
                        company_name=name,
                        contact_person=contact,
                        phone=phone,
                        address=addr,
                        opening_balance=open_bal,
                        current_balance=open_bal,
                        notes=notes,
                        is_active=True
                    )
                    self.supplier_repo.create(s)

                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save supplier:\n{str(e)}")

    class SupplierPaymentDialog(QDialog):
        """Record cash or bank payment towards a supplier's outstanding ledger balance."""
        def __init__(self, supplier, supplier_repo, parent=None):
            super().__init__(parent)
            self.supplier = supplier
            self.supplier_repo = supplier_repo
            self.setWindowTitle(f"Pay Supplier: {supplier.company_name}")
            self.resize(420, 320)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            layout.addWidget(QLabel(f"<b>Supplier:</b> {self.supplier.company_name} ({self.supplier.code})"))
            bal_lbl = QLabel(f"<b>Current Outstanding Payable:</b> <span style='color:#dc2626; font-size:14px; font-weight:bold;'>Rs. {self.supplier.current_balance:,.2f}</span>")
            layout.addWidget(bal_lbl)

            self.amount_spin = QDoubleSpinBox()
            self.amount_spin.setRange(1.0, 100000000.0)
            self.amount_spin.setValue(float(max(Decimal("0.00"), self.supplier.current_balance)))
            form.addRow("Payment Amount (Rs.)*:", self.amount_spin)

            self.method_combo = QComboBox()
            self.method_combo.addItems(["Cash (Drawer Till)", "Bank / Online Transfer", "Cheque / Pay Order"])
            form.addRow("Payment Method*:", self.method_combo)

            self.notes_input = QLineEdit()
            self.notes_input.setPlaceholderText("e.g. Paid cash at shop counter against Mill Invoice")
            form.addRow("Remarks / Slip #:", self.notes_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)

            save = QPushButton("Record Payment (ادائیگی درج کریں)")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.on_pay)

            btn_box.addWidget(cancel)
            btn_box.addStretch()
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

        def on_pay(self):
            amt = to_decimal(self.amount_spin.value())
            method = self.method_combo.currentText()
            notes = self.notes_input.text().strip() or "Counter payment"
            full_note = f"{method} - {notes}"

            try:
                self.supplier_repo.pay_supplier(self.supplier.id, amt, full_note)
                QMessageBox.information(
                    self, "Payment Recorded",
                    f"Payment of Rs. {amt:,.2f} recorded for {self.supplier.company_name}!"
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")

    class SupplierLedgerDialog(QDialog):
        """Displays running ledger statement of purchases and payments for a supplier."""
        def __init__(self, supplier, supplier_repo, parent=None):
            super().__init__(parent)
            self.supplier = supplier
            self.supplier_repo = supplier_repo
            self.setWindowTitle(f"Supplier Ledger Statement: {supplier.company_name}")
            self.resize(780, 500)
            self.init_ui()
            self.load_data()

        def init_ui(self):
            layout = QVBoxLayout(self)

            top_box = QHBoxLayout()
            info = QLabel(f"<b>Supplier:</b> {self.supplier.company_name} ({self.supplier.code}) | <b>Balance:</b> Rs. {self.supplier.current_balance:,.2f}")
            info.setStyleSheet("font-size: 13px; color: #064e3b;")
            top_box.addWidget(info)
            top_box.addStretch()

            export_btn = QPushButton("Export Ledger (CSV)")
            export_btn.clicked.connect(self.on_export)
            top_box.addWidget(export_btn)
            layout.addLayout(top_box)

            self.table = QTableWidget()
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "Date", "Transaction Type", "Debit (Paid)", "Credit (Billed)", "Balance (Payable)", "Description"
            ])
            self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
            layout.addWidget(self.table)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn, alignment=Qt.AlignRight)

        def load_data(self):
            self.entries = self.supplier_repo.get_supplier_ledger(self.supplier.id)
            self.table.setRowCount(len(self.entries))
            for i, e in enumerate(self.entries):
                dt_str = str(e["created_at"])[:19]
                deb = e["debit"]
                cred = e["credit"]
                bal = e["running_balance"]

                self.table.setItem(i, 0, QTableWidgetItem(dt_str))
                self.table.setItem(i, 1, QTableWidgetItem(str(e["transaction_type"]).upper()))

                deb_item = QTableWidgetItem(f"{deb:,.2f}" if deb > 0 else "-")
                if deb > 0:
                    deb_item.setForeground(QColor("#059669"))
                self.table.setItem(i, 2, deb_item)

                cred_item = QTableWidgetItem(f"{cred:,.2f}" if cred > 0 else "-")
                if cred > 0:
                    cred_item.setForeground(QColor("#dc2626"))
                self.table.setItem(i, 3, cred_item)

                bal_item = QTableWidgetItem(f"{bal:,.2f}")
                font = bal_item.font()
                font.setBold(True)
                bal_item.setFont(font)
                self.table.setItem(i, 4, bal_item)

                self.table.setItem(i, 5, QTableWidgetItem(e["description"] or "-"))

        def on_export(self):
            dest, _ = QFileDialog.getSaveFileName(
                self, "Export Supplier Ledger", f"{self.supplier.code}_Ledger.csv", "CSV Files (*.csv)"
            )
            if not dest:
                return

            with open(dest, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([f"SUPPLIER STATEMENT: {self.supplier.company_name} ({self.supplier.code})"])
                writer.writerow(["Date", "Type", "Debit (Paid)", "Credit (Billed)", "Balance", "Description"])
                for e in self.entries:
                    writer.writerow([
                        str(e["created_at"])[:19],
                        e["transaction_type"],
                        f"{e['debit']:.2f}",
                        f"{e['credit']:.2f}",
                        f"{e['running_balance']:.2f}",
                        e["description"] or ""
                    ])

            QMessageBox.information(self, "Export Complete", f"Ledger saved to:\n{dest}")

    class PurchaseInvoiceDialog(QDialog):
        """Comprehensive dialog to enter a supplier purchase bill with line items and stock receiving."""
        def __init__(self, supplier_repo, catalog_repo, parent=None):
            super().__init__(parent)
            self.supplier_repo = supplier_repo
            self.catalog_repo = catalog_repo
            self.setWindowTitle("Record Purchase Bill from Supplier (سپلائر خریداری بل)")
            self.resize(760, 560)
            self.items = []
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(10)

            # Header Details
            header_box = QHBoxLayout()

            self.supp_combo = QComboBox()
            self.suppliers = self.supplier_repo.get_all()
            for s in self.suppliers:
                self.supp_combo.addItem(f"{s.company_name} ({s.code})", s.id)
            header_box.addWidget(QLabel("Supplier / Mill*:"))
            header_box.addWidget(self.supp_combo)

            header_box.addWidget(QLabel("Bill / Invoice #*:"))
            self.inv_input = QLineEdit()
            import datetime
            self.inv_input.setText(f"BILL-{datetime.datetime.now().strftime('%y%m%d%H%M')}")
            header_box.addWidget(self.inv_input)

            layout.addLayout(header_box)

            # Item Entry Bar
            item_box = QHBoxLayout()
            self.prod_combo = QComboBox()
            self.all_prods = self.catalog_repo.get_products()
            self.prod_map = []
            for p in self.all_prods:
                if p.variants:
                    for v in p.variants:
                        self.prod_combo.addItem(f"{p.name} - {v.display_title()} ({v.sku})", (p, v))
                        self.prod_map.append((p, v))
                else:
                    self.prod_combo.addItem(f"{p.name} ({p.code})", (p, None))
                    self.prod_map.append((p, None))

            self.prod_combo.currentIndexChanged.connect(self.on_prod_select)

            self.qty_spin = QDoubleSpinBox()
            self.qty_spin.setRange(0.1, 100000.0)
            self.qty_spin.setValue(10.0)

            self.cost_spin = QDoubleSpinBox()
            self.cost_spin.setRange(0.0, 1000000.0)
            self.cost_spin.setValue(100.0)

            add_item_btn = QPushButton("➕ Add Line")
            add_item_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 12px;")
            add_item_btn.clicked.connect(self.on_add_line)

            item_box.addWidget(QLabel("Item:"))
            item_box.addWidget(self.prod_combo, stretch=2)
            item_box.addWidget(QLabel("Qty:"))
            item_box.addWidget(self.qty_spin)
            item_box.addWidget(QLabel("Unit Cost (Rs.):"))
            item_box.addWidget(self.cost_spin)
            item_box.addWidget(add_item_btn)
            layout.addLayout(item_box)
            self.on_prod_select()

            # Line items Table
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels([
                "Item Name & Variety", "Quantity", "Unit Cost (Rs.)", "Line Total (Rs.)", "Action"
            ])
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            layout.addWidget(self.table)

            # Bill Totals & Payment Box
            tot_box = QFormLayout()

            self.lbl_subtotal = QLabel("<b>Rs. 0.00</b>")
            tot_box.addRow("Subtotal:", self.lbl_subtotal)

            self.paid_spin = QDoubleSpinBox()
            self.paid_spin.setRange(0.0, 100000000.0)
            self.paid_spin.setValue(0.0)
            self.paid_spin.valueChanged.connect(self.update_totals)
            tot_box.addRow("Cash Paid Now (Rs.):", self.paid_spin)

            self.lbl_balance = QLabel("<b style='color:#dc2626; font-size:14px;'>Rs. 0.00</b>")
            tot_box.addRow("Balance Due (Payable):", self.lbl_balance)

            layout.addLayout(tot_box)

            # Bottom Action
            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)

            save = QPushButton("Save & Receive Stock (بل محفوظ کریں اور سٹاک بڑھائیں)")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 10px 20px;")
            save.clicked.connect(self.on_save_purchase)

            btn_box.addWidget(cancel)
            btn_box.addStretch()
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

        def on_prod_select(self):
            data = self.prod_combo.currentData()
            if data:
                p, v = data
                cost = v.cost_price if v else p.base_cost_price
                self.cost_spin.setValue(float(cost))

        def on_add_line(self):
            data = self.prod_combo.currentData()
            if not data:
                return
            p, v = data
            qty = to_qty_decimal(self.qty_spin.value())
            cost = to_decimal(self.cost_spin.value())
            line_tot = qty * cost

            self.items.append({
                "product": p,
                "variant": v,
                "product_id": p.id,
                "variant_id": v.id if v else None,
                "title": f"{p.name} ({v.display_title() if v else 'Standard'})",
                "quantity": qty,
                "unit_price": cost,
                "line_total": line_tot
            })
            self.refresh_table()

        def refresh_table(self):
            self.table.setRowCount(len(self.items))
            for i, it in enumerate(self.items):
                self.table.setItem(i, 0, QTableWidgetItem(it["title"]))
                self.table.setItem(i, 1, QTableWidgetItem(f"{it['quantity']:g}"))
                self.table.setItem(i, 2, QTableWidgetItem(f"{it['unit_price']:,.2f}"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{it['line_total']:,.2f}"))

                del_btn = QPushButton("Remove")
                del_btn.setStyleSheet("color: #dc2626;")
                del_btn.clicked.connect(lambda _, row=i: self.on_remove_line(row))
                self.table.setCellWidget(i, 4, del_btn)

            self.update_totals()

        def on_remove_line(self, row):
            if 0 <= row < len(self.items):
                self.items.pop(row)
                self.refresh_table()

        def update_totals(self):
            subtot = sum(it["line_total"] for it in self.items)
            paid = to_decimal(self.paid_spin.value())
            bal = max(Decimal("0.00"), subtot - paid)

            self.lbl_subtotal.setText(f"<b>Rs. {subtot:,.2f}</b>")
            self.lbl_balance.setText(f"<b style='color:#dc2626; font-size:14px;'>Rs. {bal:,.2f}</b>")

        def on_save_purchase(self):
            if not self.items:
                QMessageBox.warning(self, "No Items", "Please add at least one line item to this purchase bill.")
                return

            inv_no = self.inv_input.text().strip()
            if not inv_no:
                QMessageBox.warning(self, "Invoice Required", "Please enter a Purchase Invoice number.")
                return

            supp_id = self.supp_combo.currentData()
            subtot = sum(it["line_total"] for it in self.items)
            paid = to_decimal(self.paid_spin.value())

            try:
                self.supplier_repo.record_purchase(
                    purchase_invoice_no=inv_no,
                    supplier_id=supp_id,
                    subtotal=subtot,
                    tax_amount=Decimal("0.00"),
                    grand_total=subtot,
                    paid_amount=paid,
                    items=self.items
                )
                QMessageBox.information(
                    self, "Purchase Saved",
                    f"Purchase invoice #{inv_no} recorded!\nAll {len(self.items)} item stock levels updated automatically."
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record purchase bill: {str(e)}")

    class SupplierScreen(QWidget):
        def __init__(self, supplier_repo, catalog_repo=None, parent=None, **kwargs):
            super().__init__(parent)
            self.supplier_repo = supplier_repo
            self.catalog_repo = catalog_repo
            self.suppliers = []
            self.purchases = []
            self.init_ui()
            self.load_all()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(10)

            title = QLabel("Suppliers & Mill Purchasing (سپلائر اور خریداریاں)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            layout.addWidget(title)

            self.tabs = QTabWidget()

            # TAB 1: Suppliers Directory & Ledgers
            supp_widget = QWidget()
            supp_layout = QVBoxLayout(supp_widget)

            top_bar = QHBoxLayout()
            self.search_supp = QLineEdit()
            self.search_supp.setPlaceholderText("Search Supplier name, code, or phone...")
            self.search_supp.textChanged.connect(self.load_suppliers)
            top_bar.addWidget(self.search_supp)
            top_bar.addStretch()

            add_supp_btn = QPushButton("➕ Add New Supplier")
            add_supp_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            add_supp_btn.clicked.connect(self.on_add_supplier)
            top_bar.addWidget(add_supp_btn)
            supp_layout.addLayout(top_bar)

            self.supp_table = QTableWidget()
            self.supp_table.setColumnCount(7)
            self.supp_table.setHorizontalHeaderLabels([
                "Code", "Company / Mill Name", "Contact Person", "Phone", "City / Address", "Payable Balance (Rs.)", "Status"
            ])
            self.supp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.supp_table.setSelectionBehavior(QTableWidget.SelectRows)
            supp_layout.addWidget(self.supp_table)

            supp_btn_box = QHBoxLayout()
            edit_supp_btn = QPushButton("✏️ Edit Supplier")
            edit_supp_btn.clicked.connect(self.on_edit_supplier)

            pay_supp_btn = QPushButton("💳 Pay Supplier (ادائیگی)")
            pay_supp_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px;")
            pay_supp_btn.clicked.connect(self.on_pay_supplier)

            ledger_btn = QPushButton("📜 View Ledger Statement (کھاتہ)")
            ledger_btn.setStyleSheet("background-color: #7c3aed; color: white; font-weight: bold; padding: 8px 14px;")
            ledger_btn.clicked.connect(self.on_view_ledger)

            deact_btn = QPushButton("🚫 Deactivate Supplier")
            deact_btn.clicked.connect(self.on_deactivate_supplier)

            supp_btn_box.addWidget(edit_supp_btn)
            supp_btn_box.addWidget(pay_supp_btn)
            supp_btn_box.addWidget(ledger_btn)
            supp_btn_box.addWidget(deact_btn)
            supp_btn_box.addStretch()
            supp_layout.addLayout(supp_btn_box)

            self.tabs.addTab(supp_widget, "🏢 Suppliers & Ledgers (سپلائرز کھاتہ جات)")

            # TAB 2: Purchase Invoices & Stock Receiving
            purch_widget = QWidget()
            purch_layout = QVBoxLayout(purch_widget)

            p_top_bar = QHBoxLayout()
            p_top_bar.addWidget(QLabel("Recent Mill Purchase Bills:"))
            p_top_bar.addStretch()

            new_purch_btn = QPushButton("🛒 Record New Purchase Bill (نیا بل)")
            new_purch_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            new_purch_btn.clicked.connect(self.on_new_purchase)
            p_top_bar.addWidget(new_purch_btn)
            purch_layout.addLayout(p_top_bar)

            self.purch_table = QTableWidget()
            self.purch_table.setColumnCount(8)
            self.purch_table.setHorizontalHeaderLabels([
                "Invoice #", "Date", "Supplier / Mill", "Total Amount (Rs.)", "Paid (Rs.)", "Balance (Rs.)", "Status", "Notes"
            ])
            self.purch_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.purch_table.setSelectionBehavior(QTableWidget.SelectRows)
            purch_layout.addWidget(self.purch_table)

            self.tabs.addTab(purch_widget, "📦 Purchase Bills & Stock Receiving (مال خریداری)")

            layout.addWidget(self.tabs)

        def load_all(self):
            self.load_suppliers()
            self.load_purchases()

        def load_suppliers(self):
            search = self.search_supp.text().strip() or None
            self.suppliers = self.supplier_repo.get_all(search=search)
            self.supp_table.setRowCount(len(self.suppliers))
            for i, s in enumerate(self.suppliers):
                bal = s.current_balance

                self.supp_table.setItem(i, 0, QTableWidgetItem(s.code))
                self.supp_table.setItem(i, 1, QTableWidgetItem(s.company_name))
                self.supp_table.setItem(i, 2, QTableWidgetItem(s.contact_person or "-"))
                self.supp_table.setItem(i, 3, QTableWidgetItem(s.phone or "-"))
                self.supp_table.setItem(i, 4, QTableWidgetItem(s.address or "-"))

                bal_item = QTableWidgetItem(f"{bal:,.2f}")
                font = bal_item.font()
                font.setBold(True)
                bal_item.setFont(font)
                if bal > 0:
                    bal_item.setForeground(QColor("#dc2626"))
                self.supp_table.setItem(i, 5, bal_item)

                self.supp_table.setItem(i, 6, QTableWidgetItem("Active" if s.is_active else "Inactive"))

        def load_purchases(self):
            self.purchases = self.supplier_repo.get_purchases()
            self.purch_table.setRowCount(len(self.purchases))
            for i, p in enumerate(self.purchases):
                bal = p["balance_amount"]

                self.purch_table.setItem(i, 0, QTableWidgetItem(p["purchase_invoice_no"]))
                self.purch_table.setItem(i, 1, QTableWidgetItem(str(p["purchase_date"])[:19]))
                self.purch_table.setItem(i, 2, QTableWidgetItem(p["supplier_name"]))
                self.purch_table.setItem(i, 3, QTableWidgetItem(f"{p['grand_total']:,.2f}"))
                self.purch_table.setItem(i, 4, QTableWidgetItem(f"{p['paid_amount']:,.2f}"))

                bal_item = QTableWidgetItem(f"{bal:,.2f}")
                if bal > 0:
                    bal_item.setForeground(QColor("#dc2626"))
                self.purch_table.setItem(i, 5, bal_item)

                self.purch_table.setItem(i, 6, QTableWidgetItem(str(p["payment_status"]).upper()))
                self.purch_table.setItem(i, 7, QTableWidgetItem(p["notes"] or "-"))

        def on_add_supplier(self):
            dlg = SupplierDialog(self.supplier_repo, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_suppliers()

        def on_edit_supplier(self):
            row = self.supp_table.currentRow()
            if row < 0 or row >= len(self.suppliers):
                QMessageBox.information(self, "Select Supplier", "Please select a supplier row to edit.")
                return
            s = self.suppliers[row]
            dlg = SupplierDialog(self.supplier_repo, supplier=s, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_suppliers()

        def on_pay_supplier(self):
            row = self.supp_table.currentRow()
            if row < 0 or row >= len(self.suppliers):
                QMessageBox.information(self, "Select Supplier", "Please select a supplier row to make a payment.")
                return
            s = self.suppliers[row]
            dlg = SupplierPaymentDialog(s, self.supplier_repo, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_all()

        def on_view_ledger(self):
            row = self.supp_table.currentRow()
            if row < 0 or row >= len(self.suppliers):
                QMessageBox.information(self, "Select Supplier", "Please select a supplier row to view ledger.")
                return
            s = self.suppliers[row]
            dlg = SupplierLedgerDialog(s, self.supplier_repo, parent=self)
            dlg.exec()

        def on_deactivate_supplier(self):
            row = self.supp_table.currentRow()
            if row < 0 or row >= len(self.suppliers):
                QMessageBox.information(self, "Select Supplier", "Please select a supplier to deactivate.")
                return
            s = self.suppliers[row]
            reply = QMessageBox.question(
                self, "Confirm Deactivate",
                f"Deactivate '{s.company_name}'? Historical purchase and ledger data will remain safe.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.supplier_repo.deactivate(s.id)
                self.load_suppliers()

        def on_new_purchase(self):
            dlg = PurchaseInvoiceDialog(self.supplier_repo, self.catalog_repo, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_all()
else:
    class SupplierScreen:
        def __init__(self, supplier_repo, catalog_repo=None, parent=None, **kwargs):
            self.supplier_repo = supplier_repo
            self.catalog_repo = catalog_repo
            self.parent = parent
