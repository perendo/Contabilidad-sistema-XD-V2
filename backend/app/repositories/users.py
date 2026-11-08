from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import User
from .base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise ValueError("El email ya está registrado")
        return user
