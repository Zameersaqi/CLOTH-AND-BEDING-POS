"""
Authentication and Session Authorization Service
"""

from typing import Optional
from app.models.entities import User
from app.repositories.user_repository import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.current_user: Optional[User] = None

    def login(self, username: str, password: str) -> Optional[User]:
        user = self.user_repo.authenticate(username, password)
        if user:
            self.current_user = user
            self.user_repo.log_audit(user.id, "LOGIN", "session", str(user.id), f"User {username} logged in")
        return user

    def logout(self):
        if self.current_user:
            self.user_repo.log_audit(self.current_user.id, "LOGOUT", "session", str(self.current_user.id), "User logged out")
        self.current_user = None

    def is_admin_or_manager(self) -> bool:
        return bool(self.current_user and self.current_user.role in ("admin", "manager"))
