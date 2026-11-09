"""
Sales Reports, Invoices & Receipt Reprinting Screen for Arooj POS
"""

from decimal import Decimal
from typing import Optional
from app.config import format_currency
from app.services.printer_service import PrinterService
from app.ui.pos_screen import ReceiptDialog

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QHeaderView, QMessageBox, QDateEdit
    )
    from PySide6.QtCore import Qt, QDate
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
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
            reprint_btn = QPushButton("Reprint Thermal Receipt (F12)")
            reprint_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 18px;")
            reprint_btn.clicked.connect(self.on_reprint)

            return_btn = QPushButton("Process Customer Return (واپسی)")
            return_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 10px 18px;")
            return_btn.clicked.connect(self.on_return)

            btn_box.addWidget(reprint_btn)
            btn_box.addWidget(return_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

        def load_invoices(self):
            cursor = self.sales_repo.conn.cursor()
            query = """
                SELECT s.id, s.invoice_number, s.sale_date, s.subtotal, s.discount_amount, s.grand_total,
                       s.paid_amount, s.balance_amount, s.payment_status, s.payment_method, s.is_returned,
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

                status_str = "Returned" if inv["is_returned"] else inv["payment_status"].capitalize()
                st_item = QTableWidgetItem(status_str)
                if inv["is_returned"]:
                    st_item.setForeground(Qt.red)
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
                receipt_str = printer.format_plain_receipt(sale_data, settings)
                dlg = ReceiptDialog(receipt_str, self)
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
