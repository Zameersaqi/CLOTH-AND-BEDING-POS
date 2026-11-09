"""
Settings Repository for Shop Profile, Receipt Configurations, Logo, and Policies
"""

import sqlite3
from typing import Dict, Any

class SettingsRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_all_settings(self) -> Dict[str, str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM business_settings;")
        return {r["key"]: r["value"] for r in cursor.fetchall()}

    def get_setting(self, key: str, default: str = "") -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM business_settings WHERE key = ?;", (key,))
        r = cursor.fetchone()
        return r[0] if r else default

    def set_setting(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO business_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
        """, (key, str(value)))
        self.conn.commit()

    def update_shop_profile(self, name: str, phone: str, address: str, footer: str, paper_width: str = "80mm", logo_path: str = ""):
        self.set_setting("shop_name", name)
        self.set_setting("shop_phone", phone)
        self.set_setting("shop_address", address)
        self.set_setting("receipt_footer_text", footer)
        self.set_setting("receipt_paper_width", paper_width)
        if logo_path is not None:
            self.set_setting("shop_logo_path", logo_path)
