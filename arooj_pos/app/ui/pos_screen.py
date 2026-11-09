"""
Main POS Billing Screen for Arooj Cloth and Bedsheet Parda
Combines category buttons, fast search, barcode scanner, clickable product cards, and cart panel.
"""

import urllib.parse
import webbrowser
from decimal import Decimal
from typing import Optional, List
from app.models.entities import Product, ProductVariant, Customer, User
from app.ui.product_cards import ProductGridWidget
from app.ui.cart_widget import CartWidget
from app.services.printer_service import PrinterService
from app.config import format_pakistani_whatsapp_number, format_currency

try:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel,
        QScrollArea, QFrame, QDialog, QTextEdit, QMessageBox, QComboBox, QInputDialog
    )
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDesktopServices, QPixmap
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class ReceiptDialog(QDialog):
        """Displays formatted receipt for preview, paper size toggle (80mm / 58mm), and triggers printing or WhatsApp dispatch."""
        def __init__(self, sale_data: dict, settings: dict, printer_service: PrinterService, customer_phone: str = "", finalize_callback=None, parent=None):
            super().__init__(parent)
            self.sale_data = sale_data
            self.settings = settings
            self.printer_service = printer_service
            self.finalize_callback = finalize_callback
            self.is_confirmation_mode = (finalize_callback is not None)
            self.customer_phone = customer_phone or sale_data.get("customer_phone") or sale_data.get("customer_whatsapp") or ""
            self.receipt_text = self.printer_service.format_plain_receipt(sale_data, settings)

            title_prefix = "Thermal Receipt Preview - Verify Bill" if self.is_confirmation_mode else "Thermal Receipt"
            self.setWindowTitle(f"{title_prefix} - Invoice {sale_data.get('invoice_number', '')}")
            self.setMinimumSize(480, 640)
            layout = QVBoxLayout(self)

            # Controls top bar: Paper width toggle & Printer selector
            ctrl_box = QHBoxLayout()

            ctrl_box.addWidget(QLabel("Width:"))
            self.width_combo = QComboBox()
            self.width_combo.addItems(["80mm Standard (48 Cols)", "58mm Compact (32 Cols)"])
            if self.printer_service.paper_width == "58mm":
                self.width_combo.setCurrentIndex(1)
            else:
                self.width_combo.setCurrentIndex(0)
            self.width_combo.currentIndexChanged.connect(self.on_width_changed)
            ctrl_box.addWidget(self.width_combo)

            ctrl_box.addSpacing(10)
            ctrl_box.addWidget(QLabel("Printer:"))
            self.printer_combo = QComboBox()
            available = self.printer_service.get_available_printers()
            self.printer_combo.addItems(available)
            default_p = self.settings.get("default_printer")
            if default_p and default_p in available:
                self.printer_combo.setCurrentText(default_p)
            ctrl_box.addWidget(self.printer_combo, stretch=1)

            layout.addLayout(ctrl_box)

            # Store Logo Preview (if configured)
            logo_path = self.settings.get("shop_logo_path")
            if logo_path and Path(logo_path).exists():
                pm = QPixmap(str(logo_path))
                if not pm.isNull():
                    logo_frame = QFrame()
                    logo_frame.setStyleSheet("background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 4px;")
                    lf_layout = QHBoxLayout(logo_frame)
                    lf_layout.setContentsMargins(0, 0, 0, 0)
                    logo_lbl = QLabel()
                    logo_lbl.setAlignment(Qt.AlignCenter)
                    logo_lbl.setPixmap(pm.scaled(180, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    lf_layout.addWidget(logo_lbl)
                    layout.addWidget(logo_frame)

            # Monospaced receipt preview text area
            self.text_area = QTextEdit()
            self.text_area.setReadOnly(True)
            self.text_area.setFontFamily("Courier New")
            self.text_area.setPlainText(self.receipt_text)
            layout.addWidget(self.text_area)

            # Action buttons
            btn_box = QHBoxLayout()

            if self.is_confirmation_mode:
                self.confirm_btn = QPushButton("✅ CONFIRM SALE & PRINT (Enter)")
                self.confirm_btn.setStyleSheet("background-color: #059669; color: white; font-size: 13px; font-weight: bold; padding: 10px 18px;")
                self.confirm_btn.setDefault(True)
                self.confirm_btn.setFocus()
                self.confirm_btn.clicked.connect(self.on_confirm_and_print)

                self.cancel_btn = QPushButton("❌ Cancel (Esc)")
                self.cancel_btn.setStyleSheet("background-color: #f1f5f9; color: #334155; font-weight: bold; padding: 10px 16px; border: 1px solid #cbd5e1;")
                self.cancel_btn.clicked.connect(self.reject)

                whatsapp_btn = QPushButton("📱 Send WhatsApp")
                whatsapp_btn.setStyleSheet("background-color: #25d366; color: white; font-weight: bold; padding: 10px 16px;")
                whatsapp_btn.clicked.connect(self.on_send_whatsapp)

                btn_box.addWidget(self.confirm_btn, stretch=2)
                btn_box.addWidget(whatsapp_btn)
                btn_box.addWidget(self.cancel_btn)
            else:
                print_btn = QPushButton("🖨️ Print Receipt (F12)")
                print_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 16px;")
                print_btn.clicked.connect(self.on_print)

                whatsapp_btn = QPushButton("📱 Send WhatsApp")
                whatsapp_btn.setStyleSheet("background-color: #25d366; color: white; font-weight: bold; padding: 10px 16px;")
                whatsapp_btn.clicked.connect(self.on_send_whatsapp)

                close_btn = QPushButton("Close")
                close_btn.clicked.connect(self.accept)

                btn_box.addWidget(print_btn)
                btn_box.addWidget(whatsapp_btn)
                btn_box.addWidget(close_btn)

            layout.addLayout(btn_box)

        def on_width_changed(self, index: int):
            new_width = "58mm" if index == 1 else "80mm"
            self.printer_service.paper_width = new_width
            self.printer_service.cols = 32 if new_width == "58mm" else 48
            self.receipt_text = self.printer_service.format_plain_receipt(self.sale_data, self.settings)
            self.text_area.setPlainText(self.receipt_text)

        def on_confirm_and_print(self):
            """Finalizes the sale in the database once, then prints the receipt."""
            if not self.finalize_callback:
                return

            # Disable buttons to prevent duplicate triggers
            self.confirm_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)

            success, msg, inv_no = self.finalize_callback(self.sale_data)
            if not success:
                QMessageBox.critical(self, "Sale Finalization Failed", msg)
                self.confirm_btn.setEnabled(True)
                self.cancel_btn.setEnabled(True)
                return

            self.sale_data["invoice_number"] = inv_no
            self.sale_data["is_draft"] = False
            self.receipt_text = self.printer_service.format_plain_receipt(self.sale_data, self.settings)
            self.text_area.setPlainText(self.receipt_text)

            selected_printer = self.printer_combo.currentText()
            p_ok, p_msg = self.printer_service.print_receipt(
                sale_data=self.sale_data,
                settings=self.settings,
                printer_name=selected_printer
            )
            if not p_ok:
                QMessageBox.warning(
                    self,
                    "Sale Confirmed - Printer Notice",
                    f"Sale confirmed as Invoice #{inv_no}!\n\nPrinter notice:\n{p_msg}\n\nYou can reprint at any time without duplicating the sale."
                )
            else:
                QMessageBox.information(self, "Sale Confirmed", f"Invoice #{inv_no} confirmed & printed successfully!")

            self.accept()

        def on_send_whatsapp(self):
            phone = self.customer_phone
            if not phone:
                val, ok = QInputDialog.getText(
                    self,
                    "Customer WhatsApp Number",
                    "Enter customer WhatsApp / Mobile number (e.g. 03001234567):",
                    QLineEdit.Normal
                )
                if not ok or not val.strip():
                    return
                phone = val.strip()

            phone_clean = format_pakistani_whatsapp_number(phone)
            inv_no = self.sale_data.get("invoice_number", "")
            dt = str(self.sale_data.get("sale_date", "")).split()[0]
            shop = self.settings.get("shop_name", "Arooj Cloth and Bedsheet Parda")
            urdu = self.settings.get("shop_name_urdu", "عروج کلوتھ اینڈ بیڈ شیٹ پردہ")
            items = self.sale_data.get("items", [])
            gt = float(self.sale_data.get("grand_total", 0))
            paid = float(self.sale_data.get("paid_amount", 0))
            bal = float(self.sale_data.get("balance_amount", 0))

            lines = [
                f"*{shop}*",
                f"*{urdu}*",
                f"🧾 *Invoice:* #{inv_no}",
                f"📅 *Date:* {dt}",
                "─────────────────",
                f"📦 *Total Items:* {len(items)}"
            ]
            for it in items[:6]:
                name = it.get("product_name", "")
                qty = float(it.get("quantity", 0))
                unit = it.get("unit_name", "")
                tot = float(it.get("line_total", 0))
                lines.append(f"• {name}: {qty:g} {unit} = Rs. {tot:,.0f}")
            if len(items) > 6:
                lines.append(f"• ... and {len(items) - 6} more item(s)")

            lines.append("─────────────────")
            lines.append(f"💰 *Grand Total:* Rs. {gt:,.2f}")
            lines.append(f"💵 *Paid Amount:* Rs. {paid:,.2f}")
            if bal > 0:
                lines.append(f"⚠️ *Balance Due:* Rs. {bal:,.2f}")
            else:
                lines.append("✅ *Payment Status:* Paid in Full")

            lines.append("")
            lines.append("Thank you for shopping with us! / تشریف آوری کا شکریہ")

            msg_text = "\n".join(lines)
            encoded = urllib.parse.quote_plus(msg_text)
            wa_url = f"https://wa.me/{phone_clean}?text={encoded}"

            # Open via Qt DesktopServices and Python webbrowser
            try:
                QDesktopServices.openUrl(QUrl(wa_url))
            except Exception:
                pass
            try:
                webbrowser.open(wa_url)
            except Exception:
                pass

            QMessageBox.information(
                self,
                "WhatsApp Receipt Dispatched",
                f"WhatsApp link opened for customer (+{phone_clean}).\nInvoice: {inv_no}\n\nLink: {wa_url[:60]}..."
            )

        def on_print(self):
            selected_printer = self.printer_combo.currentText()
            success, msg = self.printer_service.print_receipt(
                sale_data=self.sale_data,
                settings=self.settings,
                printer_name=selected_printer
            )
            if success:
                QMessageBox.information(self, "Receipt Printed", msg)
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Printing Error",
                    f"{msg}\n\nNote: The sale is already safely committed to the database (Invoice #{self.sale_data.get('invoice_number')}). You can reprint at any time without duplicating the sale."
                )

    class PosScreen(QWidget):
        def __init__(self, catalog_repo, sales_service, settings_repo, current_user=None, customer_repo=None, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.sales_service = sales_service
            self.settings_repo = settings_repo
            self.current_user = current_user
            self.customer_repo = customer_repo
            self.selected_category_id: Optional[int] = None
            self.last_sale_phone: str = ""
            self.init_ui()
            self.load_categories()
            self.load_products()

        def init_ui(self):
            main_layout = QHBoxLayout(self)
            main_layout.setContentsMargins(8, 8, 8, 8)
            main_layout.setSpacing(8)

            # LEFT AREA: Categories, Search, Barcode, Product Cards
            left_area = QVBoxLayout()
            left_area.setSpacing(8)

            # Top Filter Bar: Barcode scan input and Text search
            filter_box = QHBoxLayout()
            filter_box.setSpacing(8)

            bc_lbl = QLabel("Scan Barcode:")
            bc_lbl.setStyleSheet("font-weight: bold;")
            self.barcode_input = QLineEdit()
            self.barcode_input.setPlaceholderText("Scan barcode or type SKU + Enter...")
            self.barcode_input.returnPressed.connect(self.on_barcode_scanned)

            search_lbl = QLabel("Search:")
            search_lbl.setStyleSheet("font-weight: bold;")
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search product by name, Urdu name, fabric...")
            self.search_input.textChanged.connect(self.on_search_changed)

            filter_box.addWidget(bc_lbl)
            filter_box.addWidget(self.barcode_input, stretch=1)
            filter_box.addWidget(search_lbl)
            filter_box.addWidget(self.search_input, stretch=1)
            left_area.addLayout(filter_box)

            # Horizontal Scroll Area for Category Buttons
            cat_scroll = QScrollArea()
            cat_scroll.setObjectName("categoryScroll")
            cat_scroll.setFixedHeight(64)
            cat_scroll.setWidgetResizable(True)
            self.cat_container = QWidget()
            self.cat_layout = QHBoxLayout(self.cat_container)
            self.cat_layout.setContentsMargins(4, 4, 4, 4)
            self.cat_layout.setSpacing(8)
            cat_scroll.setWidget(self.cat_container)
            left_area.addWidget(cat_scroll)

            # Product Cards Grid
            self.product_grid = ProductGridWidget()
            self.product_grid.product_selected.connect(self.on_product_selected)
            left_area.addWidget(self.product_grid, stretch=1)

            main_layout.addLayout(left_area, stretch=3)

            # RIGHT AREA: Cart Panel
            self.cart_widget = CartWidget(
                sales_service=self.sales_service,
                settings_repo=self.settings_repo,
                current_user=self.current_user,
                customer_repo=self.customer_repo
            )
            self.cart_widget.setObjectName("cartPanel")
            self.cart_widget.setMinimumWidth(440)
            self.cart_widget.preview_requested.connect(self.on_preview_requested)
            self.cart_widget.sale_completed_with_phone.connect(self.on_sale_completed_with_phone)
            self.cart_widget.sale_completed.connect(self.on_sale_completed)

            main_layout.addWidget(self.cart_widget, stretch=2)

        def load_categories(self):
            # All Categories button
            all_btn = QPushButton("All Categories (سب)")
            all_btn.setProperty("class", "categoryBtn active")
            all_btn.clicked.connect(lambda: self.select_category(None, all_btn))
            self.cat_layout.addWidget(all_btn)
            self.category_buttons = [all_btn]

            cats = self.catalog_repo.get_categories(only_active=True)
            for c in cats:
                urdu = f" ({c.name_urdu})" if c.name_urdu else ""
                btn = QPushButton(f"{c.name}{urdu}")
                btn.setProperty("class", "categoryBtn")
                btn.clicked.connect(lambda _, cat_id=c.id, b=btn: self.select_category(cat_id, b))
                self.cat_layout.addWidget(btn)
                self.category_buttons.append(btn)

            self.cat_layout.addStretch()

        def select_category(self, cat_id: Optional[int], clicked_btn: QPushButton):
            self.selected_category_id = cat_id
            for btn in self.category_buttons:
                btn.setProperty("class", "categoryBtn")
                btn.setStyleSheet("")
            clicked_btn.setProperty("class", "categoryBtn active")
            clicked_btn.setStyleSheet("background-color: #059669; color: white;")
            self.load_products()

        def load_products(self):
            search = self.search_input.text().strip()
            prods = self.catalog_repo.get_products(
                category_id=self.selected_category_id,
                search_term=search if search else None
            )
            self.product_grid.set_products(prods)

        def on_search_changed(self):
            self.load_products()

        def on_barcode_scanned(self):
            code = self.barcode_input.text().strip()
            if not code:
                return
            found = self.catalog_repo.find_by_barcode(code)
            if found:
                prod = self.catalog_repo.get_product_by_id(found["product_id"])
                var = None
                if found.get("variant_id"):
                    vars_list = self.catalog_repo.get_variants_for_product(prod.id)
                    var = next((v for v in vars_list if v.id == found["variant_id"]), None)
                self.cart_widget.add_item(prod, var, Decimal("1.000"))
                self.barcode_input.clear()
            else:
                QMessageBox.warning(self, "Item Not Found", f"No product or variant found matching barcode: {code}")
                self.barcode_input.selectAll()

        def on_product_selected(self, product: Product, variant: Optional[ProductVariant], quantity: Decimal):
            self.cart_widget.add_item(product, variant, quantity)

        def on_preview_requested(self, draft_sale: dict, customer_phone: str):
            """Displays the pre-sale receipt preview modal. Sale is finalized ONLY if confirmed."""
            settings = self.settings_repo.get_all_settings()
            printer = PrinterService(paper_width=settings.get("receipt_paper_width", "80mm"))
            dlg = ReceiptDialog(
                sale_data=draft_sale,
                settings=settings,
                printer_service=printer,
                customer_phone=customer_phone,
                finalize_callback=self.cart_widget.finalize_sale,
                parent=self
            )
            dlg.exec()
            self.load_products()

        def on_sale_completed_with_phone(self, invoice_number: str, phone: str):
            self.last_sale_phone = phone
            self.on_sale_completed(invoice_number)

        def on_sale_completed(self, invoice_number: str):
            # Refresh products to reflect deducted stock
            self.load_products()
else:
    class ReceiptDialog:
        def __init__(self, sale_data=None, settings=None, printer_service=None, customer_phone="", parent=None):
            self.sale_data = sale_data or {}
            self.settings = settings or {}
            self.customer_phone = customer_phone
            self.printer_service = printer_service

        def exec(self):
            return 1

    class PosScreen:
        pass
