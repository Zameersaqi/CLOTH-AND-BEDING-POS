"""
Dashboard Screen for Arooj POS: Financial Analytics, Profit Calculation,
Recent Sales Ledger, Receivables, Expenses, and Inventory Stats.
Strictly connected to live SQLite database records.
"""

import csv
from decimal import Decimal
from typing import Optional
from pathlib import Path
from app.config import format_currency, to_decimal

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
        QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QScrollArea,
        QFileDialog, QMessageBox
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
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
                    padding: 10px;
                }}
            """)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(3)

            t_box = QHBoxLayout()
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #475569;")
            u_lbl = QLabel(title_urdu)
            u_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
            t_box.addWidget(t_lbl)
            t_box.addStretch()
            t_box.addWidget(u_lbl)
            layout.addLayout(t_box)

            v_lbl = QLabel(value)
            v_lbl.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {color_hex}; font-family: monospace, sans-serif;")
            layout.addWidget(v_lbl)

            s_lbl = QLabel(subtext)
            s_lbl.setStyleSheet("font-size: 10px; color: #64748b;")
            layout.addWidget(s_lbl)

    class DashboardScreen(QWidget):
        def __init__(self, report_service, parent=None):
            super().__init__(parent)
            self.report_service = report_service
            self.recent_sales_cache = []
            self.init_ui()

        def init_ui(self):
            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(0, 0, 0, 0)

            # Scroll Area to comfortably fit KPIs, Recent Sales, and Breakdowns
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)

            content_widget = QWidget()
            layout = QVBoxLayout(content_widget)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(16)

            # Top bar with title and refresh button
            top_box = QHBoxLayout()
            title_box = QVBoxLayout()
            t = QLabel("📈 Financial & Profit Analytics (کاروباری مالیات و منافع)")
            t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            sub_t = QLabel("Real-time revenue, cost of goods, gross profit, and live store transactions")
            sub_t.setStyleSheet("font-size: 12px; color: #64748b;")
            title_box.addWidget(t)
            title_box.addWidget(sub_t)
            top_box.addLayout(title_box)

            top_box.addStretch()

            refresh_btn = QPushButton("🔄 Refresh (ریفریش)")
            refresh_btn.setStyleSheet("background-color: #059669; color: white; padding: 7px 16px; font-weight: bold; border-radius: 6px;")
            refresh_btn.clicked.connect(self.load_data)
            top_box.addWidget(refresh_btn)
            layout.addLayout(top_box)

            # Metrics Grid (8 KPI cards in 2 rows of 4)
            self.metrics_grid = QGridLayout()
            self.metrics_grid.setSpacing(10)
            layout.addLayout(self.metrics_grid)

            # Section: Recent Sales & Invoices
            sales_header_box = QHBoxLayout()
            sales_title = QLabel("🧾 Recent Sales & Invoices (حالیہ بل اور سیلز)")
            sales_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
            sales_header_box.addWidget(sales_title)
            sales_header_box.addStretch()

            export_btn = QPushButton("📥 Export Sales (.csv)")
            export_btn.setStyleSheet("background-color: #0284c7; color: white; padding: 6px 14px; font-weight: bold; border-radius: 6px;")
            export_btn.clicked.connect(self.on_export_sales_csv)
            sales_header_box.addWidget(export_btn)
            layout.addLayout(sales_header_box)

            self.recent_sales_table = QTableWidget()
            self.recent_sales_table.setColumnCount(8)
            self.recent_sales_table.setHorizontalHeaderLabels([
                "Invoice #", "Date & Time", "Customer", "WhatsApp / Phone",
                "Grand Total", "Paid", "Balance Due", "Status"
            ])
            self.recent_sales_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.recent_sales_table.setMinimumHeight(240)
            self.recent_sales_table.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;")
            layout.addWidget(self.recent_sales_table)

            # Split Tables: Top Products & Category Breakdown
            tables_box = QHBoxLayout()
            tables_box.setSpacing(16)

            # Top Products
            tp_box = QVBoxLayout()
            tp_box.addWidget(QLabel("<b>🏆 Top Selling Products (سب سے زیادہ فروخت اشیاء)</b>"))
            self.tp_table = QTableWidget()
            self.tp_table.setColumnCount(3)
            self.tp_table.setHorizontalHeaderLabels(["Product", "Quantity", "Total Sales"])
            self.tp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tp_table.setMinimumHeight(180)
            tp_box.addWidget(self.tp_table)
            tables_box.addLayout(tp_box)

            # Categories
            cat_box = QVBoxLayout()
            cat_box.addWidget(QLabel("<b>📊 Sales by Category (کیٹیگری کے لحاظ سے سیلز)</b>"))
            self.cat_table = QTableWidget()
            self.cat_table.setColumnCount(3)
            self.cat_table.setHorizontalHeaderLabels(["Category", "Units Sold", "Revenue"])
            self.cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.cat_table.setMinimumHeight(180)
            cat_box.addWidget(self.cat_table)
            tables_box.addLayout(cat_box)

            layout.addLayout(tables_box)

            scroll.setWidget(content_widget)
            root_layout.addWidget(scroll)

            self.load_data()

        def load_data(self):
            summary = self.report_service.get_dashboard_summary()

            # Clear metrics grid
            while self.metrics_grid.count():
                it = self.metrics_grid.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()

            # Primary Financial Row (Matching Preview Tab 4)
            c1 = MetricCard("Total Sales Invoices", "کل سیلز بل", str(summary["invoice_count"]), "Active POS recorded sessions", "#059669")
            c2 = MetricCard("Gross Revenue", "کل آمدنی", format_currency(summary["total_revenue"]), "Total billed to customers", "#0284c7")
            c3 = MetricCard("Cost of Goods (COGS)", "لاگت برائے فروخت", format_currency(summary["cogs"]), "Master inventory cost", "#d97706")
            c4 = MetricCard("Gross Profit", "کل منافع", format_currency(summary["gross_profit"]), "Revenue minus COGS", "#16a34a")

            # Secondary Operations Row
            c5 = MetricCard("Cash Collected (Till)", "کیش وصولی دراز", format_currency(summary["cash_collected"]), "Total cash collected today", "#0d9488")
            c6 = MetricCard("Customer Receivables", "گاہکوں کے بقایا جات", format_currency(summary["customer_receivables"]), "Outstanding credit ledger", "#b45309")
            c7 = MetricCard("Shop Expenses", "دکان کے اخراجات", format_currency(summary["expenses"]), "Recorded operational expenses", "#dc2626")
            c8 = MetricCard("Inventory Valuation", "موجودہ سٹاک مالیت", format_currency(summary["inventory_cost_value"]), f"{summary['inventory_units']:g} units on hand", "#4f46e5")

            cards = [c1, c2, c3, c4, c5, c6, c7, c8]
            for idx, card in enumerate(cards):
                row = idx // 4
                col = idx % 4
                self.metrics_grid.addWidget(card, row, col)

            # Load Recent Sales from SQLite
            sales = self.report_service.get_recent_sales(25)
            self.recent_sales_cache = sales
            self.recent_sales_table.setRowCount(len(sales))
            for i, s in enumerate(sales):
                inv_text = s["invoice_number"]
                if s.get("is_revised"):
                    inv_text += f" [Rev v{s.get('revision_count', 0) + 1}]"
                inv_item = QTableWidgetItem(inv_text)
                inv_item.setFont(QFont("monospace", 9, QFont.Bold))
                inv_item.setForeground(QColor("#059669"))
                self.recent_sales_table.setItem(i, 0, inv_item)

                self.recent_sales_table.setItem(i, 1, QTableWidgetItem(str(s["sale_date"])))
                self.recent_sales_table.setItem(i, 2, QTableWidgetItem(str(s["customer_name"])))
                self.recent_sales_table.setItem(i, 3, QTableWidgetItem(str(s.get("customer_phone") or "-")))

                gt_item = QTableWidgetItem(format_currency(s["grand_total"]))
                gt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                gt_item.setFont(QFont("monospace", 9, QFont.Bold))
                self.recent_sales_table.setItem(i, 4, gt_item)

                paid_item = QTableWidgetItem(format_currency(s["paid_amount"]))
                paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.recent_sales_table.setItem(i, 5, paid_item)

                bal = to_decimal(s["balance_amount"])
                bal_item = QTableWidgetItem(format_currency(bal))
                bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if bal > Decimal("0"):
                    bal_item.setForeground(QColor("#dc2626"))
                    bal_item.setFont(QFont("monospace", 9, QFont.Bold))
                self.recent_sales_table.setItem(i, 6, bal_item)

                status_str = "PAID" if bal <= Decimal("0") else ("PARTIAL" if s["paid_amount"] > 0 else "UNPAID")
                stat_item = QTableWidgetItem(status_str)
                stat_item.setTextAlignment(Qt.AlignCenter)
                stat_item.setForeground(QColor("#059669" if status_str == "PAID" else "#d97706"))
                stat_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.recent_sales_table.setItem(i, 7, stat_item)

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

        def on_export_sales_csv(self):
            if not self.recent_sales_cache:
                QMessageBox.information(self, "No Sales Records", "No sales records available to export.")
                return

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Sales Report",
                "sales_report.csv",
                "CSV Files (*.csv)"
            )
            if not path:
                return

            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Invoice Number", "Date & Time", "Customer Name", "Phone",
                        "Payment Method", "Grand Total", "Paid Amount", "Balance Due", "Status"
                    ])
                    for s in self.recent_sales_cache:
                        bal = float(s["balance_amount"])
                        status = "PAID" if bal <= 0 else ("PARTIAL" if s["paid_amount"] > 0 else "UNPAID")
                        writer.writerow([
                            s["invoice_number"],
                            s["sale_date"],
                            s["customer_name"],
                            s.get("customer_phone") or "",
                            s["payment_method"],
                            f"{float(s['grand_total']):.2f}",
                            f"{float(s['paid_amount']):.2f}",
                            f"{bal:.2f}",
                            status
                        ])
                QMessageBox.information(self, "Export Successful", f"Sales report exported successfully to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export CSV:\n{str(e)}")
else:
    class DashboardScreen:
        pass

