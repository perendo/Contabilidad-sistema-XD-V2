from sqlalchemy.orm import Session

from ..models import Account, ThirdParty
from .base import BaseRepository


class ThirdPartyRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, ThirdParty)

    def get_by_account_and_company(self, account_id: int, company_id):
        return self.db.query(ThirdParty).filter(
            ThirdParty.account_id == account_id, ThirdParty.company_id == company_id
        ).first()

    def list_by_company(
        self,
        company_id,
        type: str | None = None,
        search: str | None = None,
    ):
        q = self.db.query(ThirdParty).filter(ThirdParty.company_id == company_id)
        if type is not None:
            q = q.filter(ThirdParty.type == type)
        if search:
            like = f"%{search}%"
            q = q.filter(
                (ThirdParty.name.ilike(like)) | (ThirdParty.tax_id.ilike(like))
            )
        return q.order_by(ThirdParty.id).all()

    def create(self, third_party_data: dict, company_id) -> ThirdParty:
        tp = ThirdParty(**third_party_data, company_id=company_id)
        self.db.add(tp)
        try:
            self.db.flush()
        except Exception:
            self.db.rollback()
            raise ValueError("No se pudo crear el tercero")
        return tp

    def get_account(self, account_id: int, company_id) -> Account | None:
        return self.db.query(Account).filter(
            Account.id == account_id, Account.company_id == company_id
        ).first()
