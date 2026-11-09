"""
Dashboard Screen for Arooj POS: Daily Sales, Profit, Receivables, Payables, and Stock Stats
"""

from decimal import Decimal
from app.config import format_currency

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
        QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class MetricCard(QFrame):
        def __init__(self, title: str, title_urdu: str, value: str, subtext: str, color_hex: str = "#059669"):
            super().__init__()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-left: 5px solid {color_hex};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            layout = QVBoxLayout(self)
            layout.setSpacing(4)

            t_box = QHBoxLayout()
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569;")
            u_lbl = QLabel(title_urdu)
            u_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
            t_box.addWidget(t_lbl)
            t_box.addStretch()
            t_box.addWidget(u_lbl)
            layout.addLayout(t_box)

            v_lbl = QLabel(value)
            v_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color_hex};")
            layout.addWidget(v_lbl)

            s_lbl = QLabel(subtext)
            s_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
            layout.addWidget(s_lbl)

    class DashboardScreen(QWidget):
        def __init__(self, report_service, parent=None):
            super().__init__(parent)
            self.report_service = report_service
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(16)

            # Top bar with refresh button
            top_box = QHBoxLayout()
            t = QLabel("Business Performance Dashboard (کاروباری رپورٹ)")
            t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            refresh_btn = QPushButton("Refresh (ریفریش)")
            refresh_btn.setStyleSheet("padding: 6px 12px; font-weight: bold;")
            refresh_btn.clicked.connect(self.load_data)
            top_box.addWidget(t)
            top_box.addStretch()
            top_box.addWidget(refresh_btn)
            layout.addLayout(top_box)

            # Metrics Grid
            self.metrics_grid = QGridLayout()
            self.metrics_grid.setSpacing(12)
            layout.addLayout(self.metrics_grid)

            # Tables Split (Top Products & Category Sales)
            tables_box = QHBoxLayout()
            tables_box.setSpacing(16)

            # Top Products
            tp_box = QVBoxLayout()
            tp_box.addWidget(QLabel("<b>Top Selling Products (سب سے زیادہ فروخت اشیاء)</b>"))
            self.tp_table = QTableWidget()
            self.tp_table.setColumnCount(3)
            self.tp_table.setHorizontalHeaderLabels(["Product", "Quantity", "Total Sales"])
            self.tp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            tp_box.addWidget(self.tp_table)
            tables_box.addLayout(tp_box)

            # Categories
            cat_box = QVBoxLayout()
            cat_box.addWidget(QLabel("<b>Sales by Category (کیٹیگری کے لحاظ سے سیلز)</b>"))
            self.cat_table = QTableWidget()
            self.cat_table.setColumnCount(3)
            self.cat_table.setHorizontalHeaderLabels(["Category", "Units Sold", "Revenue"])
            self.cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            cat_box.addWidget(self.cat_table)
            tables_box.addLayout(cat_box)

            layout.addLayout(tables_box)
            self.load_data()

        def load_data(self):
            summary = self.report_service.get_dashboard_summary()

            # Clear metrics grid
            while self.metrics_grid.count():
                it = self.metrics_grid.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()

            # Add metric cards
            c1 = MetricCard("Today's Revenue", "آج کی فروخت", format_currency(summary["total_revenue"]), f"{summary['invoice_count']} invoices recorded", "#059669")
            c2 = MetricCard("Gross Profit", "کل منافع", format_currency(summary["gross_profit"]), f"COGS: {format_currency(summary['cogs'])}", "#0284c7")
            c3 = MetricCard("Shop Expenses", "دکان کے اخراجات", format_currency(summary["expenses"]), "Recorded operational expenses", "#dc2626")
            c4 = MetricCard("Estimated Net Profit", "خالص منافع", format_currency(summary["net_profit"]), "Revenue - COGS - Expenses", "#16a34a")

            c5 = MetricCard("Cash Collected", "کیش وصولی", format_currency(summary["cash_collected"]), "Total cash in till today", "#0d9488")
            c6 = MetricCard("Customer Receivables", "گاہکوں کے بقایا جات", format_currency(summary["customer_receivables"]), "Outstanding credit ledger", "#d97706")
            c7 = MetricCard("Supplier Payables", "سپلائر واجب الادا", format_currency(summary["supplier_payables"]), "Total debt to textile mills", "#ea580c")
            c8 = MetricCard("Inventory Valuation", "موجودہ سٹاک مالیت", format_currency(summary["inventory_cost_value"]), f"{summary['inventory_units']:g} units on hand", "#4f46e5")

            cards = [c1, c2, c3, c4, c5, c6, c7, c8]
            for idx, card in enumerate(cards):
                row = idx // 4
                col = idx % 4
                self.metrics_grid.addWidget(card, row, col)

            # Load Top Products
            top_prods = self.report_service.get_top_selling_products(5)
            self.tp_table.setRowCount(len(top_prods))
            for i, p in enumerate(top_prods):
                self.tp_table.setItem(i, 0, QTableWidgetItem(p["product_name"]))
                self.tp_table.setItem(i, 1, QTableWidgetItem(f"{p['total_qty']:g} {p['unit_name']}"))
                self.tp_table.setItem(i, 2, QTableWidgetItem(format_currency(p["total_sales"])))

            # Load Category Sales
            cats = self.report_service.get_sales_by_category()
            self.cat_table.setRowCount(len(cats))
            for i, c in enumerate(cats):
                self.cat_table.setItem(i, 0, QTableWidgetItem(f"{c['category_name']} ({c['name_urdu'] or ''})"))
                self.cat_table.setItem(i, 1, QTableWidgetItem(str(c["units_sold"])))
                self.cat_table.setItem(i, 2, QTableWidgetItem(format_currency(c["total_revenue"])))
else:
    class DashboardScreen:
        pass
