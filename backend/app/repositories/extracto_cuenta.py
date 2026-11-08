from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from ..models import Account, JournalEntry, JournalLine


class ExtractoCuentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_account(self, account_id: int, company_id=None):
        q = self.db.query(Account).filter(Account.id == account_id)
        if company_id is not None:
            q = q.filter(Account.company_id == company_id)
        return q.first()

    def movements(self, account_id: int, company_id=None, date_from=None, date_to=None):
        q = (
            self.db.query(JournalLine)
            .options(joinedload(JournalLine.entry))
            .join(JournalEntry)
            .filter(
                JournalLine.account_id == account_id,
                JournalEntry.status == "accepted",
            )
        )
        if company_id is not None:
            q = q.filter(JournalEntry.company_id == company_id)
        if date_from is not None:
            q = q.filter(JournalEntry.date >= date_from)
        if date_to is not None:
            q = q.filter(JournalEntry.date <= date_to)
        return q.order_by(JournalEntry.date, JournalEntry.id).all()
