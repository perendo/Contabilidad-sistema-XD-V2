from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Invoice, ReceivedInvoice


class IVALiquidationRepository:
    def __init__(self, db: Session):
        self.db = db

    def vat_totals(self, model, company_id, date_from, date_to):
        q = self.db.query(
            model.vat_rate,
            func.coalesce(func.sum(model.vat_amount), 0),
        ).filter(model.company_id == company_id)
        if date_from is not None:
            q = q.filter(model.date >= date_from)
        if date_to is not None:
            q = q.filter(model.date <= date_to)
        return {
            Decimal(str(rate)): Decimal(str(total))
            for rate, total in q.group_by(model.vat_rate).all()
        }
