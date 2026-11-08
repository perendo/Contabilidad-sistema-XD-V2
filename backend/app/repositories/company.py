from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Account, Company, CompanyMembership
from .base import BaseRepository


class CompanyRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Company)

    def get_by_id(self, company_id: int) -> Company | None:
        return self.db.query(Company).filter(Company.id == company_id).first()

    def get_any(self) -> Company | None:
        return self.db.query(Company).first()

    def list_by_user(self, user_id: int):
        memberships = (
            self.db.query(CompanyMembership)
            .filter(CompanyMembership.user_id == user_id)
            .all()
        )
        company_ids = [m.company_id for m in memberships]
        if not company_ids:
            return []
        return (
            self.db.query(Company)
            .filter(Company.id.in_(company_ids))
            .order_by(Company.id)
            .all()
        )

    def count_accounts(self, company_id: int) -> int:
        return (
            self.db.query(Account)
            .filter(Account.company_id == company_id)
            .count()
        )

    def create(self, company_data: dict) -> Company:
        company = Company(**company_data)
        self.db.add(company)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Conflicto al guardar la empresa")
        return company


class CompanyMembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user_and_company(self, user_id: int, company_id: int):
        return (
            self.db.query(CompanyMembership)
            .filter(
                CompanyMembership.user_id == user_id,
                CompanyMembership.company_id == company_id,
            )
            .first()
        )

    def create(self, user_id: int, company_id: int, role: str = "admin") -> CompanyMembership:
        membership = CompanyMembership(
            user_id=user_id, company_id=company_id, role=role
        )
        self.db.add(membership)
        self.db.flush()
        return membership
