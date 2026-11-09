"""
Test Authentication, PBKDF2 Password Hashing, Role Verification, and Security Hardening
"""

import unittest
import tempfile
from pathlib import Path

from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories.user_repository import UserRepository

class TestAuthSecurity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_auth.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.user_repo = UserRepository(self.conn)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_pbkdf2_hash_and_verification(self):
        password = "SecureOwnerPassword2026!"
        hashed = self.user_repo.hash_password(password)

        self.assertIn("$", hashed, "Stored hash must contain salt and hash separated by $")
        salt, h = hashed.split("$", 1)
        self.assertEqual(len(salt), 32, "Salt should be 32 hex chars (16 bytes)")
        self.assertEqual(len(h), 64, "SHA-256 hash should be 64 hex chars")

        self.assertTrue(self.user_repo.verify_password(password, hashed))
        self.assertFalse(self.user_repo.verify_password("WrongPassword", hashed))

    def test_user_authentication(self):
        # Default seeded admin user has password 'admin'
        admin = self.user_repo.authenticate("admin", "admin")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin")
        self.assertEqual(admin.role.lower(), "admin")

        # Wrong password
        failed = self.user_repo.authenticate("admin", "invalidpass")
        self.assertIsNone(failed)

        # Nonexistent user
        no_user = self.user_repo.authenticate("nonexistent_user", "somepass")
        self.assertIsNone(no_user)

    def test_update_password_requires_correct_old_password(self):
        admin = self.user_repo.get_by_username("admin")
        self.assertIsNotNone(admin)

        # Attempt update with incorrect old password
        success, msg = self.user_repo.update_password(admin.id, "wrong_old_pwd", "NewPass999#")
        self.assertFalse(success)
        self.assertIn("Current password is incorrect", msg)

        # Update with correct old password
        success2, msg2 = self.user_repo.update_password(admin.id, "admin", "NewPass999#")
        self.assertTrue(success2)

        # Verify old password no longer works
        self.assertIsNone(self.user_repo.authenticate("admin", "admin123"))

        # Verify new password works
        updated_admin = self.user_repo.authenticate("admin", "NewPass999#")
        self.assertIsNotNone(updated_admin)

    def test_set_admin_credentials_and_pin(self):
        # Set custom owner password and manager PIN during setup wizard
        success, msg = self.user_repo.set_admin_credentials(
            new_password="OwnerMasterSecret2026",
            manager_pin="9876"
        )
        self.assertTrue(success)

        # Verify login with new password
        admin = self.user_repo.authenticate("admin", "OwnerMasterSecret2026")
        self.assertIsNotNone(admin)

        # Verify manager PIN
        self.assertTrue(self.user_repo.verify_pin("9876"))
        self.assertFalse(self.user_repo.verify_pin("0000"))

if __name__ == "__main__":
    unittest.main()
