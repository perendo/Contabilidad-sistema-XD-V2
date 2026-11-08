import bcrypt

from ..repositories.users import UserRepository
from ..schemas.users import UserIn


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self, data: UserIn):
        if data.password is None or len(data.password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        password_hash = bcrypt.hashpw(
            data.password.encode(), bcrypt.gensalt()
        ).decode()
        user = self.repo.create(data.email, password_hash)
        self.repo.commit()
        self.repo.refresh(user)
        return user

    def list_users(self, limit: int = 50, offset: int = 0):
        return self.repo.list(offset=offset, limit=limit)
