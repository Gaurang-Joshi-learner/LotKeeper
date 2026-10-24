"""Registration and login."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.services.base import BaseService
from app.services.errors import AuthError, ConflictError


class AuthService(BaseService):
    def register(self, email: str, password: str, role: str = "user") -> User:
        email = email.strip().lower()
        if self.db.scalar(select(User).where(User.email == email)):
            raise ConflictError("An account with this email already exists")
        user = User(email=email, password_hash=hash_password(password), role=role)
        try:
            with self._tx():
                self.db.add(user)
        except IntegrityError:  # lost a race with a concurrent registration
            raise ConflictError("An account with this email already exists")
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.db.scalar(select(User).where(User.email == email.strip().lower()))
        # Same message for unknown email and wrong password: don't leak which accounts exist.
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Incorrect email or password")
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        return create_access_token(user.id)
