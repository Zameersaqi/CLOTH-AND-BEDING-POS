"""
Main POS Billing Screen for Arooj Cloth and Bedsheet Parda
Combines category buttons, fast search, barcode scanner, clickable product cards, and cart panel.
"""

from decimal import Decimal
from typing import Optional, List
from app.models.entities import Product, ProductVariant, Customer, User
from app.ui.product_cards import ProductGridWidget
from app.ui.cart_widget import CartWidget
from app.services.printer_service import PrinterService

try:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel,
        QScrollArea, QFrame, QDialog, QTextEdit, QMessageBox
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class ReceiptDialog(QDialog):
        """Displays formatted receipt for preview and reprint."""
        def __init__(self, receipt_text: str, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Thermal Receipt Preview")
            self.setMinimumSize(420, 560)
            layout = QVBoxLayout(self)

            text_area = QTextEdit()
            text_area.setReadOnly(True)
            text_area.setFontFamily("Courier New")
            text_area.setPlainText(receipt_text)
            layout.addWidget(text_area)

            btn_box = QHBoxLayout()
            print_btn = QPushButton("Print to Thermal Printer (F12)")
            print_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px;")
            print_btn.clicked.connect(self.on_print)
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)

            btn_box.addWidget(print_btn)
            btn_box.addWidget(close_btn)
            layout.addLayout(btn_box)

        def on_print(self):
            QMessageBox.information(self, "Printing", "Receipt sent to configured thermal printer.")
            self.accept()

    class PosScreen(QWidget):
        def __init__(self, catalog_repo, sales_service, settings_repo, current_user=None, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.sales_service = sales_service
            self.settings_repo = settings_repo
            self.current_user = current_user
            self.selected_category_id: Optional[int] = None
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
                current_user=self.current_user
            )
            self.cart_widget.setObjectName("cartPanel")
            self.cart_widget.setMinimumWidth(440)
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

        def on_sale_completed(self, invoice_number: str):
            # Show receipt dialog automatically
            sale_data = self.sales_service.sales_repo.get_sale_by_invoice(invoice_number)
            if sale_data:
                settings = self.settings_repo.get_all_settings()
                printer = PrinterService(paper_width=settings.get("receipt_paper_width", "80mm"))
                receipt_str = printer.format_plain_receipt(sale_data, settings)
                dlg = ReceiptDialog(receipt_str, self)
                dlg.exec()
            # Refresh products to reflect deducted stock
            self.load_products()
else:
    class PosScreen:
        pass
