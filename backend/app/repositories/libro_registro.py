from datetime import date

from sqlalchemy.orm import Session, joinedload

from ..models import Invoice, ReceivedInvoice


class LibroRegistroRepository:
    def __init__(self, db: Session):
        self.db = db

    def emitidas(self, company_id, year: int):
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.third_party))
            .filter(Invoice.company_id == company_id, Invoice.year == year)
            .all()
        )

    def recibidas(self, company_id, year: int):
        return (
            self.db.query(ReceivedInvoice)
            .options(joinedload(ReceivedInvoice.third_party))
            .filter(
                ReceivedInvoice.company_id == company_id,
                ReceivedInvoice.date >= date(year, 1, 1),
                ReceivedInvoice.date <= date(year, 12, 31),
            )
            .all()
        )
