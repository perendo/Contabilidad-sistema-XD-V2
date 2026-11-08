from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Invoice, ReceivedInvoice, ThirdParty


class Modelo347Repository:
    def __init__(self, db: Session):
        self.db = db

    def totals_query(self, model, company_id, date_from, date_to):
        return (
            self.db.query(
                model.third_party_id.label("third_party_id"),
                func.sum(model.total).label("total"),
            )
            .filter(
                model.company_id == company_id,
                model.date >= date_from,
                model.date <= date_to,
            )
            .group_by(model.third_party_id)
        )

    def compute(self, year: int, threshold: float, company_id):
        date_from = date(year, 1, 1)
        date_to = date(year, 12, 31)
        totals = (
            self.totals_query(Invoice, company_id, date_from, date_to)
            .union_all(
                self.totals_query(ReceivedInvoice, company_id, date_from, date_to)
            )
            .subquery()
        )

        rows = (
            self.db.query(
                ThirdParty.id,
                ThirdParty.tax_id,
                ThirdParty.name,
                func.sum(totals.c.total).label("total_annual"),
            )
            .join(totals, totals.c.third_party_id == ThirdParty.id)
            .filter(ThirdParty.company_id == company_id)
            .group_by(ThirdParty.id, ThirdParty.tax_id, ThirdParty.name)
            .having(func.sum(totals.c.total) > Decimal(str(threshold)))
            .order_by(ThirdParty.tax_id)
            .all()
        )
        return {
            "year": year,
            "threshold": threshold,
            "third_parties": [
                {
                    "third_party_id": third_party_id,
                    "tax_id": tax_id,
                    "name": name,
                    "total_annual": float(total_annual),
                }
                for third_party_id, tax_id, name, total_annual in rows
            ],
        }
