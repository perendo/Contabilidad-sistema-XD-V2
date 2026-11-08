from datetime import date
from decimal import Decimal

from sqlalchemy import case, extract, func, or_
from sqlalchemy.orm import Session

from ..models import Invoice, ReceivedInvoice, ThirdParty


class Modelo347Repository:
    def __init__(self, db: Session):
        self.db = db

    def _mes_expr(self, model):
        return extract("month", model.date)

    def totals_query(self, model, company_id, date_from, date_to):
        mes = self._mes_expr(model)
        return (
            self.db.query(
                model.third_party_id.label("third_party_id"),
                func.sum(case((mes.in_([1, 2, 3]), model.total), else_=0)).label(
                    "total_q1"
                ),
                func.sum(case((mes.in_([4, 5, 6]), model.total), else_=0)).label(
                    "total_q2"
                ),
                func.sum(case((mes.in_([7, 8, 9]), model.total), else_=0)).label(
                    "total_q3"
                ),
                func.sum(case((mes.in_([10, 11, 12]), model.total), else_=0)).label(
                    "total_q4"
                ),
                func.sum(model.total).label("total_annual"),
            )
            .filter(
                model.company_id == company_id,
                model.date >= date_from,
                model.date <= date_to,
                or_(model.irpf_rate.is_(None), model.irpf_rate == 0),
                or_(model.irpf_amount.is_(None), model.irpf_amount == 0),
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
                func.sum(totals.c.total_q1).label("total_q1"),
                func.sum(totals.c.total_q2).label("total_q2"),
                func.sum(totals.c.total_q3).label("total_q3"),
                func.sum(totals.c.total_q4).label("total_q4"),
                func.sum(totals.c.total_annual).label("total_annual"),
            )
            .join(totals, totals.c.third_party_id == ThirdParty.id)
            .filter(ThirdParty.company_id == company_id)
            .group_by(ThirdParty.id, ThirdParty.tax_id, ThirdParty.name)
            .having(func.sum(totals.c.total_annual) > Decimal(str(threshold)))
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
                    "total_q1": float(total_q1),
                    "total_q2": float(total_q2),
                    "total_q3": float(total_q3),
                    "total_q4": float(total_q4),
                    "total_annual": float(total_annual),
                }
                for third_party_id, tax_id, name, total_q1, total_q2, total_q3, total_q4, total_annual in rows
            ],
        }
