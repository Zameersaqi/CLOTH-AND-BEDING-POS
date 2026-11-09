"""
Theme Manager for Arooj Cloth and Bedsheet Parda Desktop POS
Provides seamless instant switching between Dark Mode (#1e1e1e) and Light Mode (#f8f9fa).
"""

LIGHT_THEME_QSS = """
/* Arooj POS - Retail Light Theme */
QMainWindow, QDialog {
    background-color: #f8f9fa;
    color: #0f172a;
    font-family: 'Segoe UI', 'SF Pro Text', Tahoma, Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #1e293b;
    font-size: 13px;
}

#headerWidget {
    background-color: #064e3b;
    border-bottom: 2px solid #047857;
    padding: 8px 16px;
}

#headerTitle {
    color: #f0fdf4;
    font-size: 20px;
    font-weight: 700;
}

#headerUrdu {
    color: #86efac;
    font-size: 15px;
    font-weight: 600;
}

#headerSubtitle {
    color: #a7f3d0;
    font-size: 12px;
}

#headerBackupBtn, #themeToggleBtn {
    background-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 700;
    font-size: 13px;
}

#headerBackupBtn:hover, #themeToggleBtn:hover {
    background-color: rgba(255, 255, 255, 0.30);
    border-color: #86efac;
    color: #f0fdf4;
}

#headerBackupBtn:pressed, #themeToggleBtn:pressed {
    background-color: rgba(255, 255, 255, 0.40);
}

/* Category Bar */
#categoryScroll {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}

QPushButton.categoryBtn {
    background-color: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton.categoryBtn:hover {
    background-color: #e2e8f0;
    border-color: #059669;
    color: #064e3b;
}

QPushButton.categoryBtn:checked, QPushButton.categoryBtn.active {
    background-color: #059669;
    color: #ffffff;
    border-color: #047857;
    font-weight: bold;
}

/* Product Cards */
QFrame.productCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px;
}

QFrame.productCard:hover {
    border: 2px solid #059669;
    background-color: #f0fdf4;
}

QLabel.cardTitle {
    font-weight: 700;
    font-size: 14px;
    color: #0f172a;
}

QLabel.cardPrice {
    font-weight: 700;
    font-size: 15px;
    color: #047857;
}

QLabel.cardStock {
    font-size: 11px;
    color: #64748b;
}

/* Cart Panel */
#cartPanel {
    background-color: #ffffff;
    border-left: 1px solid #e2e8f0;
    border-radius: 8px;
}

#summaryBox {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
}

/* Inputs & Form Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #059669;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 2px solid #059669;
    background-color: #ffffff;
}

/* Buttons */
QPushButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton#completeSaleBtn {
    background-color: #059669;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 800;
    padding: 12px 20px;
}

QPushButton#completeSaleBtn:hover {
    background-color: #047857;
}

QPushButton#themeToggleBtn {
    background-color: #065f46;
    color: #f0fdf4;
    border: 1px solid #34d399;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton#themeToggleBtn:hover {
    background-color: #047857;
    border-color: #6ee7b7;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #d1fae5;
    selection-color: #064e3b;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #334155;
    padding: 8px;
    font-weight: 700;
    border: none;
    border-bottom: 2px solid #cbd5e1;
}

/* Tabs */
QTabBar::tab {
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 700;
    color: #334155;
    background: transparent;
}

QTabBar::tab:selected {
    color: #064e3b;
    border-bottom: 3px solid #059669;
    background: #ecfdf5;
}

QTabBar::tab:hover:!selected {
    color: #047857;
    background: #f1f5f9;
}

QStatusBar {
    background-color: #f1f5f9;
    color: #475569;
    border-top: 1px solid #e2e8f0;
}
"""

DARK_THEME_QSS = """
/* Arooj POS - Retail Dark Theme (#1e1e1e) */
QMainWindow, QDialog {
    background-color: #1e1e1e;
    color: #f8fafc;
    font-family: 'Segoe UI', 'SF Pro Text', Tahoma, Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: transparent;
    color: #e2e8f0;
    font-size: 13px;
}

#headerWidget {
    background-color: #111827;
    border-bottom: 2px solid #0d9488;
    padding: 8px 16px;
}

#headerTitle {
    color: #f0fdf4;
    font-size: 20px;
    font-weight: 700;
}

#headerUrdu {
    color: #2dd4bf;
    font-size: 15px;
    font-weight: 600;
}

#headerSubtitle {
    color: #99f6e4;
    font-size: 12px;
}

#headerBackupBtn, #themeToggleBtn {
    background-color: #1f2937;
    color: #f3f4f6;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 700;
    font-size: 13px;
}

#headerBackupBtn:hover, #themeToggleBtn:hover {
    background-color: #374151;
    border-color: #2dd4bf;
    color: #ffffff;
}

#headerBackupBtn:pressed, #themeToggleBtn:pressed {
    background-color: #4b5563;
}

/* Category Bar */
#categoryScroll {
    background-color: #18181b;
    border-bottom: 1px solid #27272a;
}

QPushButton.categoryBtn {
    background-color: #27272a;
    color: #e4e4e7;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton.categoryBtn:hover {
    background-color: #3f3f46;
    border-color: #0d9488;
    color: #2dd4bf;
}

QPushButton.categoryBtn:checked, QPushButton.categoryBtn.active {
    background-color: #0d9488;
    color: #ffffff;
    border-color: #14b8a6;
    font-weight: bold;
}

/* Product Cards */
QFrame.productCard {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 10px;
    padding: 8px;
}

QFrame.productCard:hover {
    border: 2px solid #14b8a6;
    background-color: #1e293b;
}

QLabel.cardTitle {
    font-weight: 700;
    font-size: 14px;
    color: #f8fafc;
}

QLabel.cardPrice {
    font-weight: 700;
    font-size: 15px;
    color: #2dd4bf;
}

QLabel.cardStock {
    font-size: 11px;
    color: #a1a1aa;
}

/* Cart Panel */
#cartPanel {
    background-color: #242424;
    border-left: 1px solid #333333;
    border-radius: 8px;
}

#summaryBox {
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 12px;
}

/* Inputs & Form Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #2a2a2a;
    color: #f8fafc;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #0d9488;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 2px solid #14b8a6;
    background-color: #303030;
}

QComboBox QAbstractItemView {
    background-color: #262626;
    color: #f8fafc;
    selection-background-color: #0d9488;
    selection-color: #ffffff;
    border: 1px solid #444444;
}

/* Buttons */
QPushButton {
    background-color: #2d2d2d;
    color: #f1f5f9;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3b3b3b;
    border-color: #0d9488;
}

QPushButton:pressed {
    background-color: #1e1e1e;
}

QPushButton#completeSaleBtn {
    background-color: #0d9488;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 800;
    padding: 12px 20px;
}

QPushButton#completeSaleBtn:hover {
    background-color: #0f766e;
}

QPushButton#themeToggleBtn {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #0d9488;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton#themeToggleBtn:hover {
    background-color: #334155;
    border-color: #2dd4bf;
}

/* Tables */
QTableWidget {
    background-color: #242424;
    alternate-background-color: #1f1f1f;
    gridline-color: #383838;
    border: 1px solid #444444;
    border-radius: 6px;
    color: #f8fafc;
    selection-background-color: #134e4a;
    selection-color: #f0fdf4;
}

QHeaderView::section {
    background-color: #1a1a1a;
    color: #e2e8f0;
    padding: 8px;
    font-weight: 700;
    border: none;
    border-bottom: 2px solid #0d9488;
}

/* Tabs */
QTabBar::tab {
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 700;
    color: #94a3b8;
    background: transparent;
}

QTabBar::tab:selected {
    color: #2dd4bf;
    border-bottom: 3px solid #0d9488;
    background: #111827;
}

QTabBar::tab:hover:!selected {
    color: #f8fafc;
    background: #27272a;
}

QStatusBar {
    background-color: #111827;
    color: #94a3b8;
    border-top: 1px solid #374151;
}
"""

def get_theme_qss(theme_name: str) -> str:
    """Returns the QSS stylesheet string for the requested theme."""
    if str(theme_name).lower() == "dark":
        return DARK_THEME_QSS
    return LIGHT_THEME_QSS
