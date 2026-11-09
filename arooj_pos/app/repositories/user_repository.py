"""
User Repository for Authentication, Authorization, Manager PINs, and Audit Logs
"""

import sqlite3
import hashlib
import os
from typing import Optional, List, Tuple
from app.models.entities import User

class UserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        if salt is None:
            new_salt = os.urandom(16).hex()
            h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(new_salt), 100000).hex()
            return f"{new_salt}${h}"
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000).hex()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        if "$" in stored_hash:
            salt, h = stored_hash.split("$", 1)
            calc_hash = self.hash_password(password, salt)
            return calc_hash == h
        return False

    def get_by_username(self, username: str) -> Optional[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1;", (username,))
        r = cursor.fetchone()
        if not r:
            return None
        return User(
            id=r["id"],
            username=r["username"],
            full_name=r["full_name"],
            role=r["role"],
            password_hash=r["password_hash"],
            salt=r["salt"],
            manager_pin=r["manager_pin"],
            is_active=bool(r["is_active"])
        )

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

    def verify_pin(self, pin: str) -> bool:
        """Alias for verify_manager_pin."""
        return self.verify_manager_pin(pin)

    def update_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Safely updates a user password verifying current password first."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "User not found."

        current_hash = self.hash_password(current_password, row["salt"])
        if current_hash != row["password_hash"]:
            return False, "Current password is incorrect."

        new_salt = os.urandom(16).hex()
        new_hash = self.hash_password(new_password, new_salt)
        cursor.execute("""
            UPDATE users SET password_hash = ?, salt = ? WHERE id = ?;
        """, (new_hash, new_salt, user_id))
        self.conn.commit()
        self.log_audit(user_id, "PASSWORD_CHANGE", "users", str(user_id), "Password changed successfully")
        return True, "Password updated successfully."

    def set_admin_credentials(self, new_password: str, new_pin: Optional[str] = None, manager_pin: Optional[str] = None) -> Tuple[bool, str]:
        """Used by setup wizard to replace initial credentials with shop owner's chosen password and PIN."""
        pin = new_pin or manager_pin or "1234"
        cursor = self.conn.cursor()
        new_salt = os.urandom(16).hex()
        new_hash = self.hash_password(new_password, new_salt)
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, salt = ?, manager_pin = ?
            WHERE username = 'admin' OR role = 'admin';
        """, (new_hash, new_salt, pin))
        # Also update fallback manager_pin in settings
        cursor.execute("""
            INSERT INTO business_settings (key, value) VALUES ('manager_pin', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """, (pin,))
        self.conn.commit()
        return True, "Admin credentials set successfully."

    def log_audit(self, user_id: Optional[int], action: str, entity: str, entity_id: str, details: str, machine: str = "localhost"):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (user_id, action, entity, entity_id, details, ip_or_machine)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, action, entity, entity_id, details, machine))
        self.conn.commit()
