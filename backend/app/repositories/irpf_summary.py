import calendar
from datetime import date

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import Invoice, ReceivedInvoice

QUARTER_MONTHS = {
    1: (1, 3),
    2: (4, 6),
    3: (7, 9),
    4: (10, 12),
}


class IRPFSummaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def quarter_dates(self, year: int, quarter: int) -> tuple[date, date]:
        start_month, end_month = QUARTER_MONTHS[quarter]
        date_from = date(year, start_month, 1)
        if end_month == 2:
            date_to = date(year, end_month, calendar.monthrange(year, end_month)[1])
        elif end_month in (4, 6, 9, 11):
            date_to = date(year, end_month, 30)
        else:
            date_to = date(year, end_month, 31)
        return date_from, date_to

    def irpf_totals(self, model, company_id, date_from, date_to):
        base, retention, count = (
            self.db.query(
                func.coalesce(func.sum(model.base_amount), 0),
                func.coalesce(func.sum(model.irpf_amount), 0),
                func.count(model.id),
            )
            .filter(
                model.company_id == company_id,
                or_(model.irpf_rate.isnot(None), model.irpf_amount > 0),
                model.date >= date_from,
                model.date <= date_to,
            )
            .one()
        )
        return base, retention, count
