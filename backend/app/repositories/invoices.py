from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Invoice


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, invoice_id: int) -> Invoice | None:
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def list(
        self,
        company_id=None,
        limit: int = 50,
        offset: int = 0,
    ):
        q = self.db.query(Invoice)
        if company_id is not None:
            q = q.filter(Invoice.company_id == company_id)
        return q.order_by(Invoice.year, Invoice.number).offset(offset).limit(limit).all()

    def add(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        return invoice

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance) -> None:
        self.db.refresh(instance)

    def max_number(self, year: int, company_id=None):
        q = self.db.query(func.max(Invoice.number)).filter(Invoice.year == year)
        if company_id is not None:
            q = q.filter(Invoice.company_id == company_id)
        return q.scalar()
