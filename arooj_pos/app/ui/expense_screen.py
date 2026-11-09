"""
Dedicated Daily Shop Expenses Screen for Arooj POS
Phase 6:
- Add, View, Edit, and Delete/Void daily expenses
- Categories (Rent, Electricity, Salaries, Transport, Packaging, Repairs, Refreshment)
- Payment Method tracking (Till Cash, Bank, Owner Cash)
- User / Cashier tracking
- Daily, Weekly, and Monthly Date Filters
- CSV Export of Expense reports
"""

import csv
from decimal import Decimal
from typing import Optional, List
from datetime import datetime, date, timedelta
from pathlib import Path

from app.config import format_currency, to_decimal
from app.models.entities import Expense

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QMessageBox, QDialog,
        QDoubleSpinBox, QFormLayout, QFileDialog, QFrame, QGroupBox
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

EXPENSE_CATEGORIES = [
    "Tea & Refreshment (چائے / پانی)",
    "Electricity & Utilities (بجلی / بل)",
    "Shop Rent (دکان کرایہ)",
    "Freight & Transport (کرایہ مال / اڈہ)",
    "Packaging & Shopping Bags (شاپنگ بیگز)",
    "Staff Salary & Daily Wage (ملازم تنخواہ / دیہاڑی)",
    "Shop Maintenance & Repairs (مرمت / خرچہ)",
    "Printing & Stationery (سٹیشنری)",
    "Other Expense (متفرق خرچہ)"
]

if PYSIDE_AVAILABLE:
    class ExpenseDialog(QDialog):
        """Dialog to Add or Edit an expense."""
        def __init__(self, expense_repo, expense=None, user_id=1, parent=None):
            super().__init__(parent)
            self.expense_repo = expense_repo
            self.expense = expense
            self.user_id = user_id
            self.is_edit = expense is not None
            self.setWindowTitle("Edit Expense (خرچہ تبدیل کریں)" if self.is_edit else "Add New Shop Expense (نیا خرچہ درج کریں)")
            self.resize(440, 360)
            self.init_ui()
            if self.is_edit:
                self.populate_data()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.cat_combo = QComboBox()
            self.cat_combo.addItems(EXPENSE_CATEGORIES)
            form.addRow("Expense Category*:", self.cat_combo)

            self.amount_spin = QDoubleSpinBox()
            self.amount_spin.setRange(1.0, 10000000.0)
            self.amount_spin.setValue(100.0)
            form.addRow("Amount (Rs.)*:", self.amount_spin)

            self.method_combo = QComboBox()
            self.method_combo.addItems(["Cash (Drawer Till)", "Bank / Online Transfer", "Personal Owner Cash"])
            form.addRow("Payment Source*:", self.method_combo)

            self.desc_input = QLineEdit()
            self.desc_input.setPlaceholderText("e.g. Paid Rs. 250 for guest tea and biscuits")
            form.addRow("Description / Notes*:", self.desc_input)

            self.ref_input = QLineEdit()
            self.ref_input.setPlaceholderText("Optional receipt / slip #")
            form.addRow("Receipt / Bill Ref:", self.ref_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)

            save = QPushButton("Save Expense (محفوظ کریں)")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.on_save)

            btn_box.addWidget(cancel)
            btn_box.addStretch()
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

        def populate_data(self):
            e = self.expense
            idx = self.cat_combo.findText(e["category"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            self.amount_spin.setValue(float(e["amount"]))

            m_idx = self.method_combo.findText(e["payment_method"])
            if m_idx >= 0:
                self.method_combo.setCurrentIndex(m_idx)

            self.desc_input.setText(e["description"] or "")
            self.ref_input.setText(e["receipt_ref"] or "")

        def on_save(self):
            desc = self.desc_input.text().strip()
            if not desc:
                QMessageBox.warning(self, "Validation Error", "Please provide a description or reason for this expense.")
                return

            cat = self.cat_combo.currentText()
            amt = to_decimal(self.amount_spin.value())
            method = self.method_combo.currentText()
            ref = self.ref_input.text().strip() or None

            try:
                if self.is_edit:
                    self.expense_repo.update_expense(
                        expense_id=self.expense["id"],
                        category=cat,
                        amount=amt,
                        payment_method=method,
                        description=desc,
                        receipt_ref=ref
                    )
                else:
                    exp = Expense(
                        id=None,
                        category=cat,
                        amount=amt,
                        payment_method=method,
                        description=desc,
                        receipt_ref=ref,
                        recorded_by=self.user_id,
                        expense_date=None
                    )
                    self.expense_repo.add_expense(exp)

                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save expense:\n{str(e)}")

    class ExpenseScreen(QWidget):
        def __init__(self, expense_repo, parent=None, **kwargs):
            super().__init__(parent)
            self.expense_repo = expense_repo
            self.current_user = kwargs.get("current_user")
            self.user_id = kwargs.get("user_id", self.current_user.id if self.current_user else 1)
            self.expenses = []
            self.init_ui()
            self.load_expenses()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Top Title
            title = QLabel("Daily Shop Expenses & Petty Cash (دکان کے اخراجات)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            layout.addWidget(title)

            # Summary Cards Frame
            self.sum_frame = QFrame()
            self.sum_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px;")
            sum_layout = QHBoxLayout(self.sum_frame)

            self.lbl_today = QLabel("<b>Today's Total:</b> Rs. 0.00")
            self.lbl_month = QLabel("<b>This Month's Total:</b> Rs. 0.00")
            self.lbl_filtered = QLabel("<b>Filtered Total:</b> Rs. 0.00")

            for lbl in [self.lbl_today, self.lbl_month, self.lbl_filtered]:
                lbl.setStyleSheet("font-size: 13px; color: #1e293b;")
                sum_layout.addWidget(lbl)
                sum_layout.addStretch()

            layout.addWidget(self.sum_frame)

            # Filter Controls
            filter_box = QHBoxLayout()

            self.date_preset = QComboBox()
            self.date_preset.addItem("Today (آج)", "today")
            self.date_preset.addItem("Yesterday (کل)", "yesterday")
            self.date_preset.addItem("This Week (موجودہ ہفتہ)", "week")
            self.date_preset.addItem("This Month (موجودہ مہینہ)", "month")
            self.date_preset.addItem("All Time (تمام ریکارڈ)", "all")
            self.date_preset.currentIndexChanged.connect(self.load_expenses)
            filter_box.addWidget(self.date_preset)

            self.cat_filter = QComboBox()
            self.cat_filter.addItem("All Categories (تمام مدات)", "All")
            for c in EXPENSE_CATEGORIES:
                self.cat_filter.addItem(c, c)
            self.cat_filter.currentIndexChanged.connect(self.load_expenses)
            filter_box.addWidget(self.cat_filter)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search description or cashier...")
            self.search_input.setFixedWidth(240)
            self.search_input.textChanged.connect(self.load_expenses)
            filter_box.addWidget(self.search_input)

            filter_box.addStretch()
            layout.addLayout(filter_box)

            # Expense Table
            self.table = QTableWidget()
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "#", "Date / Time", "Category", "Amount (Rs.)", "Payment Method", "Description", "Recorded By"
            ])
            self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.doubleClicked.connect(self.on_edit_expense)
            layout.addWidget(self.table)

            # Action Buttons
            btn_box = QHBoxLayout()
            add_btn = QPushButton("➕ Add New Expense (نیا خرچہ)")
            add_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 18px; font-size: 13px;")
            add_btn.clicked.connect(self.on_add_expense)

            edit_btn = QPushButton("✏️ Edit Selected Expense")
            edit_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px 14px;")
            edit_btn.clicked.connect(self.on_edit_expense)

            del_btn = QPushButton("🗑️ Delete / Void Expense")
            del_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 10px 14px;")
            del_btn.clicked.connect(self.on_delete_expense)

            export_btn = QPushButton("📤 Export Expenses (CSV)")
            export_btn.clicked.connect(self.on_export_csv)

            btn_box.addWidget(add_btn)
            btn_box.addWidget(edit_btn)
            btn_box.addWidget(del_btn)
            btn_box.addWidget(export_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

        def get_dates_for_preset(self, preset: str):
            today = date.today()
            if preset == "today":
                return today.isoformat(), today.isoformat()
            elif preset == "yesterday":
                yest = today - timedelta(days=1)
                return yest.isoformat(), yest.isoformat()
            elif preset == "week":
                start_w = today - timedelta(days=today.weekday())
                return start_w.isoformat(), today.isoformat()
            elif preset == "month":
                start_m = date(today.year, today.month, 1)
                return start_m.isoformat(), today.isoformat()
            return None, None

        def load_expenses(self):
            preset = self.date_preset.currentData()
            start_d, end_d = self.get_dates_for_preset(preset)
            cat = self.cat_filter.currentData()
            search = self.search_input.text().strip().lower()

            all_exp = self.expense_repo.get_expenses(start_date=start_d, end_date=end_d, category=cat)

            if search:
                all_exp = [
                    e for e in all_exp if search in str(e["description"]).lower() or search in str(e["user_name"] or "").lower()
                ]

            self.expenses = all_exp

            # Summary figures
            today_iso = date.today().isoformat()
            today_sum = self.expense_repo.get_summary(start_date=today_iso, end_date=today_iso)["total_expenses"]

            month_start = date(date.today().year, date.today().month, 1).isoformat()
            month_sum = self.expense_repo.get_summary(start_date=month_start, end_date=today_iso)["total_expenses"]

            filtered_sum = sum(Decimal(str(e["amount"])) for e in self.expenses)

            self.lbl_today.setText(f"<b>Today's Total:</b> Rs. {today_sum:,.2f}")
            self.lbl_month.setText(f"<b>This Month's Total:</b> Rs. {month_sum:,.2f}")
            self.lbl_filtered.setText(f"<b>Filtered Total ({len(self.expenses)} entries):</b> Rs. {filtered_sum:,.2f}")

            self.table.setRowCount(len(self.expenses))
            for i, e in enumerate(self.expenses):
                dt_str = str(e["expense_date"])[:19]
                amt = Decimal(str(e["amount"]))

                self.table.setItem(i, 0, QTableWidgetItem(str(e["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(dt_str))
                self.table.setItem(i, 2, QTableWidgetItem(e["category"]))

                amt_item = QTableWidgetItem(f"{amt:,.2f}")
                font = amt_item.font()
                font.setBold(True)
                amt_item.setFont(font)
                amt_item.setForeground(QColor("#b91c1c"))
                self.table.setItem(i, 3, amt_item)

                self.table.setItem(i, 4, QTableWidgetItem(e["payment_method"]))
                self.table.setItem(i, 5, QTableWidgetItem(e["description"] or "-"))
                self.table.setItem(i, 6, QTableWidgetItem(e["user_name"] or "Cashier"))

        def on_add_expense(self):
            dlg = ExpenseDialog(self.expense_repo, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_expenses()

        def on_edit_expense(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.expenses):
                QMessageBox.information(self, "Select Expense", "Please select an expense entry to edit.")
                return
            exp = self.expenses[row]
            dlg = ExpenseDialog(self.expense_repo, expense=exp, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_expenses()

        def on_delete_expense(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.expenses):
                QMessageBox.information(self, "Select Expense", "Please select an expense entry to delete.")
                return
            exp = self.expenses[row]
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete this expense of Rs. {exp['amount']:,.2f} ({exp['category']})?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.expense_repo.delete_expense(exp["id"])
                self.load_expenses()

        def on_export_csv(self):
            dest, _ = QFileDialog.getSaveFileName(
                self, "Export Expenses", "Expenses_Report.csv", "CSV Files (*.csv)"
            )
            if not dest:
                return

            with open(dest, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Category", "Amount (Rs.)", "Payment Method", "Description", "Recorded By"])
                for e in self.expenses:
                    writer.writerow([
                        e["id"],
                        str(e["expense_date"])[:19],
                        e["category"],
                        f"{Decimal(str(e['amount'])):.2f}",
                        e["payment_method"],
                        e["description"] or "",
                        e["user_name"] or ""
                    ])

            QMessageBox.information(self, "Export Complete", f"Expenses saved successfully to:\n{dest}")
else:
    class ExpenseScreen:
        def __init__(self, expense_repo, parent=None, **kwargs):
            self.expense_repo = expense_repo
            self.parent = parent
