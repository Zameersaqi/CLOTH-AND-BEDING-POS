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
        sale_completed_with_phone = Signal(str, str)  # invoice number, customer phone
        preview_requested = Signal(dict, str)  # draft sale data, customer phone
        hold_requested = Signal()

        def __init__(self, sales_service, settings_repo, current_user=None, customer_repo=None, parent=None):
            super().__init__(parent)
            self.sales_service = sales_service
            self.settings_repo = settings_repo
            self.current_user = current_user
            self.customer_repo = customer_repo
            self.cart_items: List[CartItem] = []
            self.price_editors: List[QLineEdit] = []
            self.selected_customer: Optional[Customer] = None
            self.customers_list: List[Customer] = []
            self.init_ui()
            self.load_customers()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)

            # Customer selection & phone panel
            cust_panel = QFrame()
            cust_panel.setObjectName("customerPanel")
            cust_layout = QVBoxLayout(cust_panel)
            cust_layout.setContentsMargins(8, 8, 8, 8)
            cust_layout.setSpacing(6)

            # Row 1: Customer Account dropdown
            row1 = QHBoxLayout()
            cust_lbl = QLabel("Customer:")
            cust_lbl.setStyleSheet("font-weight: bold; min-width: 65px;")
            self.customer_combo = QComboBox()
            self.customer_combo.currentIndexChanged.connect(self.on_customer_changed)

            self.clear_cart_btn = QPushButton("Clear Cart")
            self.clear_cart_btn.setProperty("class", "dangerBtn")
            self.clear_cart_btn.setStyleSheet("color: #ef4444; font-weight: bold;")
            self.clear_cart_btn.clicked.connect(self.clear_cart)

            row1.addWidget(cust_lbl)
            row1.addWidget(self.customer_combo, stretch=1)
            row1.addWidget(self.clear_cart_btn)
            cust_layout.addLayout(row1)

            # Row 2: WhatsApp / Phone # input
            row2 = QHBoxLayout()
            phone_lbl = QLabel("WhatsApp:")
            phone_lbl.setStyleSheet("font-weight: bold; min-width: 65px;")
            self.phone_input = QLineEdit()
            self.phone_input.setPlaceholderText("WhatsApp / Mobile # (e.g. 03001234567)")
            row2.addWidget(phone_lbl)
            row2.addWidget(self.phone_input, stretch=1)
            cust_layout.addLayout(row2)

            layout.addWidget(cust_panel)

            # Cart Items Table - Compact 6-Column Layout (Always visible without horizontal scrolling)
            self.table = QTableWidget()
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "Product", "Variant", "Qty", "Price (Rs.)", "Total (Rs.)", ""
            ])
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.table.setColumnWidth(3, 92)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
            self.table.setColumnWidth(5, 34)
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
            self.discount_input.returnPressed.connect(self.on_discount_enter)
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
            self.tendered_input.returnPressed.connect(self.on_tendered_enter)
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

        def load_customers(self):
            """Populates customer dropdown from customer repository."""
            if not hasattr(self, "customer_combo"):
                return
            self.customer_combo.blockSignals(True)
            self.customer_combo.clear()
            self.customer_combo.addItem("Walk-in Customer (کاؤنٹر گاہک)", userData=None)
            self.customers_list = []
            if self.customer_repo:
                try:
                    self.customers_list = self.customer_repo.get_all()
                    for c in self.customers_list:
                        bal_info = f" [Bal: Rs. {c.current_balance:,.0f}]" if c.current_balance > Decimal("0") else ""
                        phone_info = f" ({c.phone})" if c.phone else ""
                        self.customer_combo.addItem(f"{c.name}{phone_info}{bal_info}", userData=c)
                except Exception:
                    pass
            self.customer_combo.blockSignals(False)

        def on_customer_changed(self, index: int):
            data = self.customer_combo.itemData(index)
            self.selected_customer = data
            if data and data.phone:
                self.phone_input.setText(data.phone)
            elif not data:
                self.phone_input.clear()

        def set_customer(self, customer: Optional[Customer]):
            self.selected_customer = customer
            if not hasattr(self, "customer_combo"):
                return
            if customer is None:
                self.customer_combo.setCurrentIndex(0)
                self.phone_input.clear()
            else:
                for idx in range(self.customer_combo.count()):
                    c = self.customer_combo.itemData(idx)
                    if c and c.id == customer.id:
                        self.customer_combo.setCurrentIndex(idx)
                        if c.phone:
                            self.phone_input.setText(c.phone)
                        break

        def add_item(self, product, variant=None, quantity=Decimal("1.000"), roll=None):
            self.sales_service.add_to_cart(self.cart_items, product, variant, quantity, roll)
            self.refresh_table()

        def refresh_table(self):
            self.price_editors = []
            self.table.setRowCount(len(self.cart_items))
            for idx, item in enumerate(self.cart_items):
                # 0: Product name
                name_item = QTableWidgetItem(item.product_name)
                name_item.setToolTip(item.product_name)
                self.table.setItem(idx, 0, name_item)

                # 1: Variant
                var_str = item.variant_title
                if item.roll_number:
                    var_str += f" (Roll #{item.roll_number})"
                var_item = QTableWidgetItem(var_str)
                self.table.setItem(idx, 1, var_item)

                # 2: Quantity
                qty_str = f"{item.quantity:g} {item.unit_name}"
                qty_item = QTableWidgetItem(qty_str)
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(idx, 2, qty_item)

                # 3: Editable selling price directly inside the row
                price_edit = QLineEdit(f"{item.transaction_price:.2f}")
                price_edit.setAlignment(Qt.AlignRight)
                price_edit.setToolTip(f"Catalog Master: Rs. {item.original_catalog_price:,.2f}\nPress ENTER to apply & jump to next item.")
                if item.is_price_overridden:
                    price_edit.setStyleSheet("background-color: #fef3c7; color: #b45309; font-weight: bold; border: 1px solid #f59e0b; border-radius: 4px; padding: 2px 4px;")
                else:
                    price_edit.setStyleSheet("font-weight: bold; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px;")

                price_edit.returnPressed.connect(lambda it=item, pe=price_edit, r=idx: self.on_inline_price_enter(it, pe, r))
                price_edit.editingFinished.connect(lambda it=item, pe=price_edit, r=idx: self.on_inline_price_commit(it, pe, r))

                self.table.setCellWidget(idx, 3, price_edit)
                self.price_editors.append(price_edit)

                # 4: Total
                tot_item = QTableWidgetItem(f"{item.line_total:,.2f}")
                tot_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                tot_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table.setItem(idx, 4, tot_item)

                # 5: Delete button
                del_btn = QPushButton("✕")
                del_btn.setToolTip("Remove Item from Cart")
                del_btn.setFixedSize(26, 24)
                del_btn.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px; background: transparent; border: 1px solid #fca5a5; border-radius: 4px;")
                del_btn.clicked.connect(lambda _, it=item: self.remove_item(it))

                del_widget = QWidget()
                del_layout = QHBoxLayout(del_widget)
                del_layout.setContentsMargins(1, 1, 1, 1)
                del_layout.setAlignment(Qt.AlignCenter)
                del_layout.addWidget(del_btn)
                self.table.setCellWidget(idx, 5, del_widget)

            self.refresh_totals()

        def on_inline_price_enter(self, item: CartItem, editor: QLineEdit, row_idx: int):
            """Commit the price and automatically focus the next item's price field with text pre-selected."""
            success = self.on_inline_price_commit(item, editor, row_idx)
            if success:
                next_row = row_idx + 1
                if next_row < len(self.price_editors):
                    next_editor = self.price_editors[next_row]
                    next_editor.setFocus()
                    next_editor.selectAll()
                else:
                    self.discount_input.setFocus()
                    self.discount_input.selectAll()

        def on_discount_enter(self):
            """Commit discount and move focus to tendered cash input with text pre-selected."""
            self.refresh_totals()
            self.tendered_input.setFocus()
            self.tendered_input.selectAll()

        def on_tendered_enter(self):
            """Validate tendered cash and open the safe receipt preview modal without finalizing."""
            self.calculate_change()
            self.request_receipt_preview()

        def on_inline_price_commit(self, item: CartItem, editor: QLineEdit, row_idx: int) -> bool:
            """Validates entered price, enforces Manager PIN when exceeding discount limit, and recalculates totals."""
            text = editor.text().strip().replace(",", "")
            try:
                new_price = to_decimal(text)
            except Exception:
                editor.setText(f"{item.transaction_price:.2f}")
                return False

            if new_price == item.transaction_price:
                return True

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
                        override_reason="Bargain / Counter Discount Approved by Manager"
                    )

            if not success:
                QMessageBox.warning(self, "Price Update Restricted", msg)
                editor.setText(f"{item.transaction_price:.2f}")
                editor.selectAll()
                return False

            # Update editor style and tooltip
            editor.setText(f"{item.transaction_price:.2f}")
            if item.is_price_overridden:
                editor.setStyleSheet("background-color: #fef3c7; color: #b45309; font-weight: bold; border: 1px solid #f59e0b; border-radius: 4px; padding: 2px 4px;")
                editor.setToolTip(f"Negotiated Price! Catalog Master: Rs. {item.original_catalog_price:,.2f}\nReason: {item.override_reason}")
            else:
                editor.setStyleSheet("font-weight: bold; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px;")
                editor.setToolTip(f"Catalog Master Price: Rs. {item.original_catalog_price:,.2f}")

            # Update line total item in table
            tot_item = self.table.item(row_idx, 4)
            if tot_item:
                tot_item.setText(f"{item.line_total:,.2f}")

            self.refresh_totals()
            return True

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

        def request_receipt_preview(self):
            """Validates payment and displays safe thermal receipt preview without finalizing or clearing cart."""
            if not self.cart_items:
                QMessageBox.warning(self, "Empty Cart", "Please add at least one product before proceeding.")
                return

            disc = to_decimal(self.discount_input.text())
            tendered = to_decimal(self.tendered_input.text())
            method = self.pay_method.currentText()
            summary = self.sales_service.calculate_cart_summary(self.cart_items, bill_discount=disc)
            gt = summary["grand_total"]

            # Validate cash payment: tender cannot be less than grand total
            if method.lower() == "cash" and tendered < gt:
                QMessageBox.warning(
                    self,
                    "Insufficient Cash Tendered",
                    f"Insufficient cash tendered!\n\nGrand Total: Rs. {gt:,.2f}\nTendered Cash: Rs. {tendered:,.2f}\nShortage: Rs. {(gt - tendered):,.2f}\n\nPlease enter the full cash amount paid by the customer."
                )
                self.tendered_input.setFocus()
                self.tendered_input.selectAll()
                return

            if "credit" in method.lower() and not self.selected_customer:
                QMessageBox.warning(
                    self,
                    "Customer Required for Credit",
                    "A registered customer must be selected to make a Credit (ادھار) sale."
                )
                return

            items_data = [
                {
                    "product_id": it.product_id,
                    "variant_id": it.variant_id,
                    "roll_id": it.roll_id,
                    "product_name": it.product_name,
                    "variant_title": it.variant_title,
                    "quantity": float(it.quantity),
                    "unit_name": it.unit_name,
                    "transaction_price": float(it.transaction_price),
                    "unit_price": float(it.transaction_price),
                    "original_catalog_price": float(it.original_catalog_price),
                    "is_price_overridden": it.is_price_overridden,
                    "override_reason": it.override_reason,
                    "line_total": float(it.line_total),
                }
                for it in self.cart_items
            ]

            import datetime
            paid_amount = gt if (method.lower() == "cash" or tendered >= gt) else tendered
            change_due = max(Decimal("0.00"), tendered - gt) if method.lower() == "cash" else Decimal("0.00")
            bal_due = max(Decimal("0.00"), gt - tendered) if "credit" in method.lower() else Decimal("0.00")

            draft_sale = {
                "invoice_number": "PREVIEW (Draft)",
                "sale_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "subtotal": float(summary["subtotal"]),
                "discount_amount": float(summary["discount_amount"]),
                "grand_total": float(gt),
                "payment_method": method,
                "paid_amount": float(paid_amount),
                "tendered_cash": float(tendered),
                "change_due": float(change_due),
                "balance_amount": float(bal_due),
                "customer_id": self.selected_customer.id if self.selected_customer else None,
                "customer_name": self.selected_customer.name if self.selected_customer else "Walk-in Customer",
                "customer_phone": self.phone_input.text().strip() or (self.selected_customer.phone if self.selected_customer else ""),
                "cashier_id": self.current_user.id if self.current_user else 1,
                "cashier_name": self.current_user.full_name if self.current_user else "Cashier",
                "items": items_data,
                "is_draft": True
            }

            customer_phone = self.phone_input.text().strip() or (self.selected_customer.phone if self.selected_customer else "")
            self.preview_requested.emit(draft_sale, customer_phone)

        def finalize_sale(self, draft_sale: dict = None) -> tuple:
            """
            Finalizes the sale in the database, deducts inventory, records customer balance,
            and clears the cart. ONLY called when the user confirms in the receipt preview.
            Returns (success, message, invoice_number).
            """
            if not self.cart_items:
                return False, "Cart is empty. Nothing to finalize.", ""

            disc = to_decimal(self.discount_input.text())
            tendered = to_decimal(self.tendered_input.text())
            method = self.pay_method.currentText()
            cust_id = self.selected_customer.id if self.selected_customer else None
            cashier_id = self.current_user.id if self.current_user else 1
            customer_phone = self.phone_input.text().strip()

            success, msg, inv_no = self.sales_service.complete_checkout(
                cart=self.cart_items,
                customer_id=cust_id,
                cashier_id=cashier_id,
                payment_method=method,
                tendered_cash=tendered,
                bill_discount=disc,
                notes=f"Customer WhatsApp/Phone: {customer_phone}" if customer_phone else ""
            )

            if success:
                self.cart_items.clear()
                self.discount_input.setText("0.00")
                self.tendered_input.setText("0.00")
                self.phone_input.clear()
                self.refresh_table()
                self.sale_completed.emit(inv_no)
                self.sale_completed_with_phone.emit(inv_no, customer_phone)
                return True, msg, inv_no
            else:
                return False, msg, ""

        def on_complete_sale(self):
            """F10 / Complete sale trigger opens the safe preview modal."""
            self.request_receipt_preview()
else:
    class CartWidget:
        pass
