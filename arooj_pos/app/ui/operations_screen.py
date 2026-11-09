"""
Operations Screen for Arooj POS:
1. Cash Drawer Shift & End-of-Day Closing (کیش کلوزنگ)
2. Daily Shop Expenses (دکان کے اخراجات)
3. Purchases & Supplier Management (سپلائر اور خریداریاں)
"""

from decimal import Decimal
from typing import Optional, List
from datetime import datetime

from app.config import format_currency, to_decimal
from app.models.entities import Expense, Supplier

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QMessageBox, QDialog,
        QDoubleSpinBox, QFormLayout, QTabWidget, QGroupBox, QFrame
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class AddExpenseDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Record Daily Shop Expense (خرچہ درج کریں)")
            self.setMinimumWidth(380)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.category_combo = QComboBox()
            self.category_combo.addItems([
                "Tea & Refreshment (چائے / پانی)",
                "Electricity & Utilities (بجلی / بل)",
                "Shop Rent (دکان کرایہ)",
                "Freight & Transport (کرایہ مال / اڈہ)",
                "Packaging & Shopping Bags (شاپنگ بیگز)",
                "Staff Salary & Daily Wage (ملازم تنخواہ / دیہاڑی)",
                "Shop Maintenance & Repairs (مرمت / خرچہ)",
                "Other Expense (متفرق خرچہ)"
            ])
            form.addRow("Expense Category:", self.category_combo)

            self.amount_spin = QDoubleSpinBox()
            self.amount_spin.setRange(1.0, 1000000.0)
            self.amount_spin.setValue(100.0)
            form.addRow("Amount (Rs.):", self.amount_spin)

            self.method_combo = QComboBox()
            self.method_combo.addItems(["Cash (Till Cash)", "Bank / Online", "Personal Owner Cash"])
            form.addRow("Payment Source:", self.method_combo)

            self.desc_input = QLineEdit()
            self.desc_input.setPlaceholderText("Description or reason...")
            form.addRow("Description:", self.desc_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            save = QPushButton("Save Expense")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.accept)

            btn_box.addWidget(cancel)
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

    class RecordPurchaseDialog(QDialog):
        def __init__(self, supplier_repo, catalog_repo, parent=None):
            super().__init__(parent)
            self.supplier_repo = supplier_repo
            self.catalog_repo = catalog_repo
            self.setWindowTitle("Record Purchase Bill from Supplier (سپلائر خریداری بل)")
            self.setMinimumWidth(440)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.supp_combo = QComboBox()
            self.suppliers = self.supplier_repo.get_all()
            for s in self.suppliers:
                self.supp_combo.addItem(f"{s.company_name} ({s.code})", s.id)
            form.addRow("Supplier / Mill:", self.supp_combo)

            self.inv_no_input = QLineEdit()
            self.inv_no_input.setPlaceholderText("e.g. MILL-INV-1092")
            form.addRow("Purchase Invoice #:", self.inv_no_input)

            self.total_spin = QDoubleSpinBox()
            self.total_spin.setRange(1.0, 10000000.0)
            self.total_spin.setValue(10000.0)
            form.addRow("Total Bill Amount (Rs.):", self.total_spin)

            self.paid_spin = QDoubleSpinBox()
            self.paid_spin.setRange(0.0, 10000000.0)
            self.paid_spin.setValue(0.0)
            form.addRow("Paid Cash Amount (Rs.):", self.paid_spin)

            self.notes_input = QLineEdit("Stock delivery arrived")
            form.addRow("Notes:", self.notes_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            save = QPushButton("Record Purchase")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.accept)

            btn_box.addWidget(cancel)
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

    class OperationsScreen(QWidget):
        def __init__(self, expense_repo, supplier_repo, sales_repo, catalog_repo, current_user=None, parent=None):
            super().__init__(parent)
            self.expense_repo = expense_repo
            self.supplier_repo = supplier_repo
            self.sales_repo = sales_repo
            self.catalog_repo = catalog_repo
            self.current_user = current_user
            self.opening_cash = Decimal("5000.00")  # Default morning cash float
            self.init_ui()

        def init_ui(self):
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(12)

            tabs = QTabWidget()

            # 1. Cash Shift & Day Closing Tab
            cash_widget = QWidget()
            cash_layout = QVBoxLayout(cash_widget)
            cash_layout.setSpacing(12)

            cash_header = QLabel("End-of-Day Cash Closing & Till Reconciliation (کاؤنٹر کیش کلوزنگ)")
            cash_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #064e3b;")
            cash_layout.addWidget(cash_header)

            reconcile_frame = QFrame()
            reconcile_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;")
            rec_layout = QFormLayout(reconcile_frame)

            self.open_cash_input = QDoubleSpinBox()
            self.open_cash_input.setRange(0.0, 1000000.0)
            self.open_cash_input.setValue(float(self.opening_cash))
            self.open_cash_input.valueChanged.connect(self.refresh_cash_closing)
            rec_layout.addRow("Morning Opening Cash Float (ابتدائی کیش):", self.open_cash_input)

            self.today_cash_sales_lbl = QLabel("Rs. 0.00")
            self.today_cash_sales_lbl.setStyleSheet("font-weight: bold; color: #047857;")
            rec_layout.addRow("Today Cash Sales Collected (سیلز کیش وصولی):", self.today_cash_sales_lbl)

            self.today_expenses_lbl = QLabel("Rs. 0.00")
            self.today_expenses_lbl.setStyleSheet("font-weight: bold; color: #dc2626;")
            rec_layout.addRow("Paid Out from Till (دکان کے اخراجات منفی):", self.today_expenses_lbl)

            self.expected_cash_lbl = QLabel("Rs. 0.00")
            self.expected_cash_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #064e3b;")
            rec_layout.addRow("Expected Cash in Drawer (دراز میں متوقع کیش):", self.expected_cash_lbl)

            self.actual_cash_input = QDoubleSpinBox()
            self.actual_cash_input.setRange(0.0, 10000000.0)
            self.actual_cash_input.setValue(0.0)
            self.actual_cash_input.valueChanged.connect(self.calculate_discrepancy)
            rec_layout.addRow("Actual Physical Cash Counted (گنا ہوا کیش):", self.actual_cash_input)

            self.discrepancy_lbl = QLabel("Rs. 0.00 (Balanced)")
            self.discrepancy_lbl.setStyleSheet("font-size: 14px; font-weight: 800;")
            rec_layout.addRow("Cash Discrepancy (فرق / کمی بیشی):", self.discrepancy_lbl)

            cash_layout.addWidget(reconcile_frame)

            close_shift_btn = QPushButton("Save & Close Cashier Shift (شفٹ بند کریں)")
            close_shift_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
            close_shift_btn.clicked.connect(self.on_close_shift)
            cash_layout.addWidget(close_shift_btn)
            cash_layout.addStretch()

            # 2. Shop Expenses Tab
            exp_widget = QWidget()
            exp_layout = QVBoxLayout(exp_widget)
            exp_layout.setSpacing(10)

            exp_top = QHBoxLayout()
            exp_top.addWidget(QLabel("<b>Recorded Daily Shop Expenses (دکان کے اخراجات)</b>"))
            exp_top.addStretch()

            add_exp_btn = QPushButton("+ Add New Expense (خرچہ درج کریں)")
            add_exp_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 14px;")
            add_exp_btn.clicked.connect(self.on_add_expense)
            exp_top.addWidget(add_exp_btn)
            exp_layout.addLayout(exp_top)

            self.exp_table = QTableWidget()
            self.exp_table.setColumnCount(5)
            self.exp_table.setHorizontalHeaderLabels(["ID", "Category", "Amount (Rs.)", "Payment Method", "Date & Time"])
            self.exp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            exp_layout.addWidget(self.exp_table)

            # 3. Suppliers & Purchases Tab
            supp_widget = QWidget()
            supp_layout = QVBoxLayout(supp_widget)
            supp_layout.setSpacing(10)

            supp_top = QHBoxLayout()
            supp_top.addWidget(QLabel("<b>Suppliers & Mill Accounts (سپلائرز کھاتہ)</b>"))
            supp_top.addStretch()

            add_purch_btn = QPushButton("+ Record Purchase Bill (خریداری بل)")
            add_purch_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px;")
            add_purch_btn.clicked.connect(self.on_record_purchase)
            supp_top.addWidget(add_purch_btn)

            supp_layout.addLayout(supp_top)

            self.supp_table = QTableWidget()
            self.supp_table.setColumnCount(5)
            self.supp_table.setHorizontalHeaderLabels(["Code", "Company / Mill", "Contact", "Phone", "Current Payable Balance"])
            self.supp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            supp_layout.addWidget(self.supp_table)

            # Assemble Tabs
            tabs.addTab(cash_widget, "💵 Cash Drawer & Shift Closing (کیش کلوزنگ)")
            tabs.addTab(exp_widget, "📝 Daily Expenses (اخراجات)")
            tabs.addTab(supp_widget, "🏭 Suppliers & Purchases (سپلائرز)")

            main_layout.addWidget(tabs)
            self.refresh_all()

        def refresh_all(self):
            self.refresh_cash_closing()
            self.load_expenses()
            self.load_suppliers()

        def refresh_cash_closing(self):
            cursor = self.sales_repo.conn.cursor()
            # Calculate today's cash sales
            cursor.execute("""
                SELECT COALESCE(SUM(paid_amount), 0)
                FROM sales
                WHERE payment_method = 'Cash' AND DATE(sale_date) = DATE('now', 'localtime') AND is_returned = 0;
            """)
            cash_sales = to_decimal(cursor.fetchone()[0])

            # Calculate today's expenses paid via Cash
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE payment_method LIKE '%Cash%' AND DATE(expense_date) = DATE('now', 'localtime');
            """)
            cash_expenses = to_decimal(cursor.fetchone()[0])

            opening = to_decimal(self.open_cash_input.value())
            expected = opening + cash_sales - cash_expenses

            self.today_cash_sales_lbl.setText(format_currency(cash_sales))
            self.today_expenses_lbl.setText(format_currency(cash_expenses))
            self.expected_cash_lbl.setText(format_currency(expected))
            self.expected_cash_val = expected
            self.calculate_discrepancy()

        def calculate_discrepancy(self):
            actual = to_decimal(self.actual_cash_input.value())
            expected = getattr(self, "expected_cash_val", Decimal("0.00"))
            diff = actual - expected

            if diff == Decimal("0.00"):
                self.discrepancy_lbl.setText("Rs. 0.00 (Perfect Match ✓)")
                self.discrepancy_lbl.setStyleSheet("color: #059669; font-size: 14px; font-weight: 800;")
            elif diff > Decimal("0.00"):
                self.discrepancy_lbl.setText(f"+Rs. {diff:,.2f} (Excess / فالتو کیش)")
                self.discrepancy_lbl.setStyleSheet("color: #0284c7; font-size: 14px; font-weight: 800;")
            else:
                self.discrepancy_lbl.setText(f"-Rs. {abs(diff):,.2f} (Short / کمی)")
                self.discrepancy_lbl.setStyleSheet("color: #dc2626; font-size: 14px; font-weight: 800;")

        def on_close_shift(self):
            actual = to_decimal(self.actual_cash_input.value())
            expected = getattr(self, "expected_cash_val", Decimal("0.00"))
            diff = actual - expected
            user_id = self.current_user.id if self.current_user else 1

            cursor = self.sales_repo.conn.cursor()
            cursor.execute("""
                INSERT INTO cash_registers (
                    cashier_id, opening_cash, total_cash_sales, total_expenses,
                    expected_cash, actual_cash, discrepancy, notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Shift closed at counter', 'closed');
            """, (
                user_id, float(self.open_cash_input.value()),
                float(self.today_cash_sales_lbl.text().replace("Rs.", "").replace(",", "").strip()),
                float(self.today_expenses_lbl.text().replace("Rs.", "").replace(",", "").strip()),
                float(expected), float(actual), float(diff)
            ))
            self.sales_repo.conn.commit()

            status_str = "Balanced" if diff == 0 else ("Short" if diff < 0 else "Excess")
            QMessageBox.information(
                self, "Shift Closed",
                f"Cash shift recorded successfully!\nExpected: Rs. {expected:,.2f}\nActual: Rs. {actual:,.2f}\nStatus: {status_str} (Rs. {diff:,.2f})"
            )

        def load_expenses(self):
            expenses = self.expense_repo.get_expenses()
            self.exp_table.setRowCount(len(expenses))
            for i, e in enumerate(expenses):
                self.exp_table.setItem(i, 0, QTableWidgetItem(str(e["id"])))
                self.exp_table.setItem(i, 1, QTableWidgetItem(e["category"]))
                self.exp_table.setItem(i, 2, QTableWidgetItem(format_currency(e["amount"])))
                self.exp_table.setItem(i, 3, QTableWidgetItem(e["payment_method"]))
                self.exp_table.setItem(i, 4, QTableWidgetItem(str(e["expense_date"])))

        def on_add_expense(self):
            dlg = AddExpenseDialog(self)
            if dlg.exec() == QDialog.Accepted:
                exp = Expense(
                    id=None,
                    category=dlg.category_combo.currentText().split("(")[0].strip(),
                    amount=to_decimal(dlg.amount_spin.value()),
                    payment_method=dlg.method_combo.currentText().split("(")[0].strip(),
                    description=dlg.desc_input.text().strip(),
                    recorded_by=self.current_user.id if self.current_user else 1
                )
                self.expense_repo.add_expense(exp)
                self.refresh_all()
                QMessageBox.information(self, "Expense Saved", f"Expense of Rs. {exp.amount:,.2f} recorded.")

        def load_suppliers(self):
            supps = self.supplier_repo.get_all()
            self.supp_table.setRowCount(len(supps))
            for i, s in enumerate(supps):
                self.supp_table.setItem(i, 0, QTableWidgetItem(s.code))
                self.supp_table.setItem(i, 1, QTableWidgetItem(s.company_name))
                self.supp_table.setItem(i, 2, QTableWidgetItem(s.contact_person or "-"))
                self.supp_table.setItem(i, 3, QTableWidgetItem(s.phone or "-"))
                self.supp_table.setItem(i, 4, QTableWidgetItem(format_currency(s.current_balance)))

        def on_record_purchase(self):
            dlg = RecordPurchaseDialog(self.supplier_repo, self.catalog_repo, self)
            if dlg.exec() == QDialog.Accepted:
                supp_id = dlg.supp_combo.currentData()
                inv_no = dlg.inv_no_input.text().strip() or f"PUR-{datetime.now().strftime('%Y%m%d%H%M')}"
                total = to_decimal(dlg.total_spin.value())
                paid = to_decimal(dlg.paid_spin.value())

                self.supplier_repo.record_purchase(
                    purchase_invoice_no=inv_no,
                    supplier_id=supp_id,
                    subtotal=total,
                    tax_amount=Decimal("0.00"),
                    grand_total=total,
                    paid_amount=paid,
                    items=[]  # General bill entry
                )
                self.load_suppliers()
                QMessageBox.information(self, "Purchase Recorded", f"Purchase invoice {inv_no} recorded for Rs. {total:,.2f}.")
else:
    class OperationsScreen:
        pass
