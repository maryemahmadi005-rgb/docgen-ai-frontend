from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def find_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.session.scalars(stmt).first()

    def find_by_github_username(self, github_username: str) -> Optional[User]:
        stmt = select(User).where(User.github_username == github_username)
        return self.session.scalars(stmt).first()

    def email_exists(self, email: str) -> bool:
        return self.find_by_email(email) is not None

    def create(
        self,
        email: str,
        password_hash: Optional[str] = None,
        github_username: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            github_username=github_username,
            github_token=github_token,
        )
        return self.add(user)

    def update_github_token(self, user: User, encrypted_token: str) -> User:
        user.github_token = encrypted_token
        self.session.flush()
        return user
