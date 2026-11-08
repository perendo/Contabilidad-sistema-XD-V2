from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Account
from ..schemas.accounts import _escape_like
from .base import BaseRepository


class AccountRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Account)

    def get_by_code(self, company_id, code: str) -> Account | None:
        return self.db.query(Account).filter(
            Account.company_id == company_id, Account.code == code
        ).first()

    def list_by_company(
        self,
        company_id,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        q = self.db.query(Account).filter(Account.company_id == company_id)
        if search:
            escaped = _escape_like(search)
            like = f"%{escaped}%"
            q = q.filter(
                (Account.code.ilike(like, escape="\\"))
                | (Account.name.ilike(like, escape="\\"))
            )
        return q.order_by(Account.code).offset(offset).limit(limit).all()

    def create(self, account_data: dict, company_id) -> Account:
        account = Account(**account_data, company_id=company_id)
        self.db.add(account)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Código de cuenta duplicado")
        return account
