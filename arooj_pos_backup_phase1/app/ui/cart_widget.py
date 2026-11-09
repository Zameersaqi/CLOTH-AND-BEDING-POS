"""
Cart Widget for Arooj POS
Displays items, quantities, editable transaction prices with visual indicators,
discounts, tax, totals, tendered cash, and payment action buttons.
"""

from decimal import Decimal
from typing import List, Optional, Callable
from app.models.entities import CartItem, Customer, User
from app.config import format_currency, to_decimal, to_qty_decimal

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QAbstractItemView,
        QMessageBox, QInputDialog, QFrame
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QColor, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    # Headless / CLI fallback
    PYSIDE_AVAILABLE = False
    QWidget = object
    Signal = lambda *args: None

if PYSIDE_AVAILABLE:
    class CartWidget(QWidget):
        sale_completed = Signal(str)  # invoice number
        hold_requested = Signal()

        def __init__(self, sales_service, settings_repo, current_user=None, parent=None):
            super().__init__(parent)
            self.sales_service = sales_service
            self.settings_repo = settings_repo
            self.current_user = current_user
            self.cart_items: List[CartItem] = []
            self.selected_customer: Optional[Customer] = None
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)

            # Header & Customer selector
            cust_box = QHBoxLayout()
            cust_label = QLabel("Customer:")
            cust_label.setStyleSheet("font-weight: bold;")
            self.cust_name_label = QLabel("Walk-in Customer (کاؤنٹر گاہک)")
            self.cust_name_label.setStyleSheet("color: #064e3b; font-weight: bold;")
            self.clear_cart_btn = QPushButton("Clear Cart")
            self.clear_cart_btn.setProperty("class", "dangerBtn")
            self.clear_cart_btn.clicked.connect(self.clear_cart)

            cust_box.addWidget(cust_label)
            cust_box.addWidget(self.cust_name_label)
            cust_box.addStretch()
            cust_box.addWidget(self.clear_cart_btn)
            layout.addLayout(cust_box)

            # Cart Items Table
            self.table = QTableWidget()
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "Item", "Variant", "Qty", "Original (Rs.)", "Rate (Rs.)", "Total (Rs.)", "Action"
            ])
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
            self.table.setColumnWidth(6, 120)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            layout.addWidget(self.table)

            # Summary Box
            summary_frame = QFrame()
            summary_frame.setObjectName("summaryBox")
            sum_layout = QVBoxLayout(summary_frame)

            # Subtotal and Discount
            r1 = QHBoxLayout()
            r1.addWidget(QLabel("Subtotal:"))
            self.subtotal_lbl = QLabel("Rs. 0.00")
            self.subtotal_lbl.setStyleSheet("font-weight: bold;")
            r1.addWidget(self.subtotal_lbl)
            r1.addSpacing(20)
            r1.addWidget(QLabel("Bill Discount (Rs.):"))
            self.discount_input = QLineEdit("0.00")
            self.discount_input.setFixedWidth(80)
            self.discount_input.textChanged.connect(self.refresh_totals)
            r1.addWidget(self.discount_input)
            sum_layout.addLayout(r1)

            # Grand Total
            r2 = QHBoxLayout()
            gt_lbl = QLabel("GRAND TOTAL:")
            gt_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
            self.grand_total_lbl = QLabel("Rs. 0.00")
            self.grand_total_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #047857;")
            r2.addWidget(gt_lbl)
            r2.addStretch()
            r2.addWidget(self.grand_total_lbl)
            sum_layout.addLayout(r2)

            # Payment inputs
            r3 = QHBoxLayout()
            r3.addWidget(QLabel("Pay Method:"))
            self.pay_method = QComboBox()
            self.pay_method.addItems(["Cash", "Credit", "Card", "Bank Transfer"])
            r3.addWidget(self.pay_method)

            r3.addWidget(QLabel("Tendered Cash:"))
            self.tendered_input = QLineEdit("0.00")
            self.tendered_input.setFixedWidth(100)
            self.tendered_input.textChanged.connect(self.calculate_change)
            r3.addWidget(self.tendered_input)

            r3.addWidget(QLabel("Change Due:"))
            self.change_lbl = QLabel("Rs. 0.00")
            self.change_lbl.setStyleSheet("font-weight: bold; color: #dc2626;")
            r3.addWidget(self.change_lbl)
            sum_layout.addLayout(r3)

            layout.addWidget(summary_frame)

            # Checkout & Hold Buttons
            btn_box = QHBoxLayout()
            self.hold_btn = QPushButton("Hold Bill (F6)")
            self.hold_btn.setProperty("class", "secondaryBtn")
            self.hold_btn.clicked.connect(self.on_hold_bill)

            self.checkout_btn = QPushButton("COMPLETE SALE (F10)")
            self.checkout_btn.setObjectName("completeSaleBtn")
            self.checkout_btn.clicked.connect(self.on_complete_sale)

            btn_box.addWidget(self.hold_btn)
            btn_box.addWidget(self.checkout_btn, stretch=2)
            layout.addLayout(btn_box)

        def set_customer(self, customer: Optional[Customer]):
            self.selected_customer = customer
            if customer:
                bal_str = f" [Bal: Rs. {customer.current_balance:,.2f}]" if customer.current_balance > 0 else ""
                self.cust_name_label.setText(f"{customer.name}{bal_str}")
            else:
                self.cust_name_label.setText("Walk-in Customer (کاؤنٹر گاہک)")

        def add_item(self, product, variant=None, quantity=Decimal("1.000"), roll=None):
            self.sales_service.add_to_cart(self.cart_items, product, variant, quantity, roll)
            self.refresh_table()

        def refresh_table(self):
            self.table.setRowCount(len(self.cart_items))
            for idx, item in enumerate(self.cart_items):
                # Product name
                name_item = QTableWidgetItem(item.product_name)
                self.table.setItem(idx, 0, name_item)

                # Variant
                var_str = item.variant_title
                if item.roll_number:
                    var_str += f" (Roll #{item.roll_number})"
                var_item = QTableWidgetItem(var_str)
                self.table.setItem(idx, 1, var_item)

                # Quantity
                qty_str = f"{item.quantity:g} {item.unit_name}"
                qty_item = QTableWidgetItem(qty_str)
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(idx, 2, qty_item)

                # Original Catalog Price
                orig_item = QTableWidgetItem(f"{item.original_catalog_price:,.2f}")
                orig_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(idx, 3, orig_item)

                # Transaction Price (Editable)
                rate_str = f"{item.transaction_price:,.2f}"
                rate_item = QTableWidgetItem(rate_str)
                rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if item.is_price_overridden:
                    rate_item.setBackground(QColor("#fef3c7"))
                    rate_item.setForeground(QColor("#b45309"))
                    rate_item.setToolTip(f"Negotiated Price! Reason: {item.override_reason}")
                self.table.setItem(idx, 4, rate_item)

                # Total
                tot_item = QTableWidgetItem(f"{item.line_total:,.2f}")
                tot_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                tot_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table.setItem(idx, 5, tot_item)

                # Actions Widget (Edit Rate, Qty, Remove)
                act_widget = QWidget()
                act_layout = QHBoxLayout(act_widget)
                act_layout.setContentsMargins(2, 2, 2, 2)
                act_layout.setSpacing(4)

                edit_price_btn = QPushButton("Rs✎")
                edit_price_btn.setToolTip("Edit Negotiated Transaction Price")
                edit_price_btn.setFixedWidth(36)
                edit_price_btn.clicked.connect(lambda _, it=item: self.prompt_edit_price(it))

                del_btn = QPushButton("✕")
                del_btn.setToolTip("Remove Item")
                del_btn.setFixedWidth(30)
                del_btn.setStyleSheet("color: #ef4444; font-weight: bold;")
                del_btn.clicked.connect(lambda _, it=item: self.remove_item(it))

                act_layout.addWidget(edit_price_btn)
                act_layout.addWidget(del_btn)
                self.table.setCellWidget(idx, 6, act_widget)

            self.refresh_totals()

        def prompt_edit_price(self, item: CartItem):
            """Prompts cashier or manager to enter a customer-negotiated transaction price."""
            val, ok = QInputDialog.getDouble(
                self,
                "Edit Transaction Price",
                f"Enter negotiated selling price for:\n{item.product_name} ({item.variant_title})\nOriginal Master Price: Rs. {item.original_catalog_price:,.2f}",
                float(item.transaction_price),
                0.0,
                1000000.0,
                2
            )
            if not ok:
                return

            new_price = to_decimal(val)
            success, msg = self.sales_service.update_cart_item_price(
                item=item,
                new_transaction_price=new_price,
                current_user=self.current_user
            )

            # If failed due to manager authorization required
            if not success and "Manager PIN" in msg:
                pin, pin_ok = QInputDialog.getText(
                    self,
                    "Manager PIN Required",
                    f"{msg}\nEnter authorized Manager PIN:",
                    QLineEdit.Password
                )
                if pin_ok and pin:
                    success, msg = self.sales_service.update_cart_item_price(
                        item=item,
                        new_transaction_price=new_price,
                        current_user=self.current_user,
                        manager_pin=pin,
                        override_reason="Customer Bargain / Shop Special Discount"
                    )

            if not success:
                QMessageBox.warning(self, "Price Update Restricted", msg)
            else:
                self.refresh_table()

        def remove_item(self, item: CartItem):
            if item in self.cart_items:
                self.cart_items.remove(item)
                self.refresh_table()

        def clear_cart(self):
            if not self.cart_items:
                return
            reply = QMessageBox.question(
                self, "Confirm Clear Cart", "Are you sure you want to clear all items from the current cart?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.cart_items.clear()
                self.refresh_table()

        def refresh_totals(self):
            disc = to_decimal(self.discount_input.text())
            summary = self.sales_service.calculate_cart_summary(self.cart_items, bill_discount=disc)
            self.subtotal_lbl.setText(format_currency(summary["subtotal"]))
            self.grand_total_lbl.setText(format_currency(summary["grand_total"]))
            # Auto populate tendered cash if empty or matching
            if self.tendered_input.text() == "0.00" or self.tendered_input.text() == "":
                self.tendered_input.setText(f"{summary['grand_total']:.2f}")
            self.calculate_change()

        def calculate_change(self):
            disc = to_decimal(self.discount_input.text())
            summary = self.sales_service.calculate_cart_summary(self.cart_items, bill_discount=disc)
            gt = summary["grand_total"]
            tendered = to_decimal(self.tendered_input.text())
            if tendered >= gt:
                change = tendered - gt
                self.change_lbl.setText(format_currency(change))
                self.change_lbl.setStyleSheet("font-weight: bold; color: #059669;")
            else:
                due = gt - tendered
                self.change_lbl.setText(f"-{format_currency(due)}")
                self.change_lbl.setStyleSheet("font-weight: bold; color: #dc2626;")

        def on_hold_bill(self):
            if not self.cart_items:
                QMessageBox.information(self, "Hold Bill", "Cart is empty. Nothing to hold.")
                return
            import json
            payload = json.dumps([
                {
                    "product_id": it.product_id, "variant_id": it.variant_id, "qty": float(it.quantity),
                    "price": float(it.transaction_price), "orig": float(it.original_catalog_price)
                } for it in self.cart_items
            ])
            import datetime
            code = f"HOLD-{datetime.datetime.now().strftime('%H%M%S')}"
            cust_id = self.selected_customer.id if self.selected_customer else None
            self.sales_service.sales_repo.hold_sale(code, cust_id, payload, "Held at counter", self.current_user.id if self.current_user else None)
            QMessageBox.information(self, "Bill Held", f"Bill held with code: {code}")
            self.cart_items.clear()
            self.refresh_table()
            self.hold_requested.emit()

        def on_complete_sale(self):
            if not self.cart_items:
                QMessageBox.warning(self, "Empty Cart", "Please add at least one product before completing sale.")
                return

            disc = to_decimal(self.discount_input.text())
            tendered = to_decimal(self.tendered_input.text())
            method = self.pay_method.currentText()
            cust_id = self.selected_customer.id if self.selected_customer else None
            cashier_id = self.current_user.id if self.current_user else 1

            success, msg, inv_no = self.sales_service.complete_checkout(
                cart=self.cart_items,
                customer_id=cust_id,
                cashier_id=cashier_id,
                payment_method=method,
                tendered_cash=tendered,
                bill_discount=disc
            )

            if success:
                QMessageBox.information(self, "Sale Recorded", f"Invoice {inv_no} recorded successfully!\n{msg}")
                self.cart_items.clear()
                self.discount_input.setText("0.00")
                self.tendered_input.setText("0.00")
                self.refresh_table()
                self.sale_completed.emit(inv_no)
            else:
                QMessageBox.critical(self, "Checkout Failed", msg)
else:
    class CartWidget:
        pass
