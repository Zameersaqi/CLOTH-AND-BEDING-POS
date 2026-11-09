"""
Customer Management & Credit Ledger Screen for Arooj POS
Manages customer profiles, outstanding credit, and payment receipts.
"""

from decimal import Decimal
from typing import Optional
from app.config import format_currency, to_decimal
from app.models.entities import Customer

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QHeaderView, QMessageBox, QDialog, QFormLayout,
        QDoubleSpinBox
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class ReceivePaymentDialog(QDialog):
        def __init__(self, customer: Customer, parent=None):
            super().__init__(parent)
            self.customer = customer
            self.setWindowTitle(f"Receive Payment: {customer.name}")
            self.setMinimumWidth(340)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            form.addRow("Customer:", QLabel(f"<b>{self.customer.name}</b> ({self.customer.phone or ''})"))
            form.addRow("Current Due Balance:", QLabel(f"<b style='color:#dc2626'>{format_currency(self.customer.current_balance)}</b>"))

            self.amount_spin = QDoubleSpinBox()
            self.amount_spin.setRange(1.0, 1000000.0)
            self.amount_spin.setValue(float(self.customer.current_balance))
            form.addRow("Payment Amount (Rs.):", self.amount_spin)

            self.notes_input = QLineEdit("Cash received against account balance")
            form.addRow("Notes / Reference:", self.notes_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            ok = QPushButton("Record Payment")
            ok.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            ok.clicked.connect(self.accept)
            btn_box.addWidget(cancel)
            btn_box.addWidget(ok)
            layout.addLayout(btn_box)

    class CustomerManagementScreen(QWidget):
        def __init__(self, customer_repo, parent=None, **kwargs):
            super().__init__(parent)
            self.customer_repo = customer_repo
            self.init_ui()
            self.load_customers()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            top_box = QHBoxLayout()
            title = QLabel("Customer Ledger & Credit Accounts (کھاتہ جات گاہک)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            top_box.addWidget(title)
            top_box.addStretch()

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search customer name or phone...")
            self.search_input.setFixedWidth(240)
            self.search_input.textChanged.connect(self.load_customers)
            top_box.addWidget(self.search_input)

            new_cust_btn = QPushButton("+ New Customer (نیا گاہک)")
            new_cust_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 12px;")
            new_cust_btn.clicked.connect(self.on_new_customer)
            top_box.addWidget(new_cust_btn)

            layout.addLayout(top_box)

            # Customer Table
            self.table = QTableWidget()
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "Code", "Customer Name", "Phone", "City", "Credit Limit", "Current Balance (Due)"
            ])
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            layout.addWidget(self.table)

            # Bottom buttons
            btn_box = QHBoxLayout()
            pay_btn = QPushButton("Receive Payment (وصولی درج کریں)")
            pay_btn.setStyleSheet("background-color: #0d9488; color: white; font-weight: bold; padding: 10px 18px;")
            pay_btn.clicked.connect(self.on_receive_payment)

            stmt_btn = QPushButton("View Account Statement (کھاتہ تفصیل)")
            stmt_btn.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 10px 18px;")
            stmt_btn.clicked.connect(self.on_view_statement)

            btn_box.addWidget(pay_btn)
            btn_box.addWidget(stmt_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

        def load_customers(self):
            search = self.search_input.text().strip()
            self.customers = self.customer_repo.get_all(search if search else None)
            self.table.setRowCount(len(self.customers))
            for i, c in enumerate(self.customers):
                self.table.setItem(i, 0, QTableWidgetItem(c.code))
                self.table.setItem(i, 1, QTableWidgetItem(c.name))
                self.table.setItem(i, 2, QTableWidgetItem(c.phone or "-"))
                self.table.setItem(i, 3, QTableWidgetItem(c.city or "Local"))
                self.table.setItem(i, 4, QTableWidgetItem(format_currency(c.credit_limit)))

                bal_item = QTableWidgetItem(format_currency(c.current_balance))
                bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if c.current_balance > Decimal("0.00"):
                    bal_item.setForeground(Qt.red)
                self.table.setItem(i, 5, bal_item)

        def on_receive_payment(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.customers):
                QMessageBox.information(self, "Select Customer", "Please select a customer to record payment.")
                return
            cust = self.customers[row]
            dlg = ReceivePaymentDialog(cust, self)
            if dlg.exec() == QDialog.Accepted:
                amt = to_decimal(dlg.amount_spin.value())
                notes = dlg.notes_input.text().strip()
                new_bal = self.customer_repo.receive_payment(cust.id, amt, "Cash", notes)
                QMessageBox.information(self, "Payment Recorded", f"Payment of Rs. {amt:,.2f} recorded!\nNew balance: Rs. {new_bal:,.2f}")
                self.load_customers()

        def on_view_statement(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.customers):
                QMessageBox.information(self, "Select Customer", "Please select a customer to view statement.")
                return
            cust = self.customers[row]
            records = self.customer_repo.get_customer_statement(cust.id)

            msg = f"Account Statement for {cust.name}\n" + ("=" * 45) + "\n"
            for r in records:
                inv = f"[{r['invoice_number']}] " if r.get("invoice_number") else ""
                msg += f"{r['created_at'][:10]} | {inv}{r['description']}\n"
                msg += f"   Debit: Rs. {r['debit']:,.2f} | Credit: Rs. {r['credit']:,.2f} | Balance: Rs. {r['running_balance']:,.2f}\n"

            QMessageBox.information(self, f"Statement: {cust.name}", msg)

        def on_new_customer(self):
            import datetime
            code = f"CUST-{datetime.datetime.now().strftime('%M%S')}"
            cust = Customer(
                id=None,
                code=code,
                name=f"Customer {code}",
                phone="0300-1112233",
                city="Local",
                notes="Created via POS"
            )
            self.customer_repo.create(cust)
            self.load_customers()

    CustomerScreen = CustomerManagementScreen
else:
    class CustomerManagementScreen:
        def __init__(self, customer_repo, parent=None, **kwargs):
            self.customer_repo = customer_repo
            self.parent = parent
    CustomerScreen = CustomerManagementScreen
