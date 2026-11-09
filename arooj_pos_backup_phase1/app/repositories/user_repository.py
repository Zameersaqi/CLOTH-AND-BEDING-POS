"""
User Repository for Authentication, Authorization, Manager PINs, and Audit Logs
"""

import sqlite3
import hashlib
import os
from typing import Optional, List
from app.models.entities import User

class UserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000).hex()

    def create_user(self, username: str, full_name: str, role: str, password: str, manager_pin: Optional[str] = None) -> int:
        salt = os.urandom(16).hex()
        pwd_hash = self.hash_password(password, salt)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, full_name, role, password_hash, salt, manager_pin, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1);
        """, (username, full_name, role, pwd_hash, salt, manager_pin))
        uid = cursor.lastrowid
        self.conn.commit()
        return uid

    def authenticate(self, username: str, password: str) -> Optional[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1;", (username,))
        r = cursor.fetchone()
        if not r:
            return None
        salt = r["salt"]
        expected_hash = self.hash_password(password, salt)
        if r["password_hash"] == expected_hash:
            return User(
                id=r["id"],
                username=r["username"],
                full_name=r["full_name"],
                role=r["role"],
                password_hash=r["password_hash"],
                salt=salt,
                manager_pin=r["manager_pin"],
                is_active=bool(r["is_active"])
            )
        return None

    def verify_manager_pin(self, pin: str) -> bool:
        """Verifies if the provided PIN belongs to an active manager or admin."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM users
            WHERE manager_pin = ? AND role IN ('admin', 'manager') AND is_active = 1;
        """, (pin,))
        if cursor.fetchone():
            return True
        # Also check fallback business_settings manager_pin
        cursor.execute("SELECT value FROM business_settings WHERE key = 'manager_pin';")
        r = cursor.fetchone()
        if r and r[0] == pin:
            return True
        return False

    def log_audit(self, user_id: Optional[int], action: str, entity: str, entity_id: str, details: str, machine: str = "localhost"):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (user_id, action, entity, entity_id, details, ip_or_machine)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, action, entity, entity_id, details, machine))
        self.conn.commit()
