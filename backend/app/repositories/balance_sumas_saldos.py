from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Account, JournalEntry, JournalLine


class BalanceSumasSaldosRepository:
    def __init__(self, db: Session):
        self.db = db

    def compute(self, company_id, date_from: date | None, date_to: date | None):
        stmt = (
            self.db.query(
                Account.code,
                Account.name,
                func.coalesce(func.sum(JournalLine.debit), 0).label("total_debe"),
                func.coalesce(func.sum(JournalLine.credit), 0).label("total_haber"),
            )
            .join(JournalLine, Account.id == JournalLine.account_id)
            .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
            .filter(JournalEntry.status == "accepted")
        )
        if company_id is not None:
            stmt = stmt.filter(
                JournalEntry.company_id == company_id,
                Account.company_id == company_id,
            )
        if date_from is not None:
            stmt = stmt.filter(JournalEntry.date >= date_from)
        if date_to is not None:
            stmt = stmt.filter(JournalEntry.date <= date_to)

        rows_db = (
            stmt.group_by(Account.id, Account.code, Account.name)
            .order_by(Account.code)
            .all()
        )

        total_debe = Decimal("0")
        total_haber = Decimal("0")
        rows = []
        for code, name, debe, haber in rows_db:
            debe_dec = Decimal(str(debe))
            haber_dec = Decimal(str(haber))
            saldo = debe_dec - haber_dec
            total_debe += debe_dec
            total_haber += haber_dec
            rows.append(
                {
                    "code": code,
                    "name": name,
                    "debe": float(debe_dec),
                    "haber": float(haber_dec),
                    "saldo": float(saldo),
                }
            )

        cuadrado = total_debe == total_haber

        return {
            "date_from": date_from,
            "date_to": date_to,
            "accounts": rows,
            "total_debe": float(total_debe),
            "total_haber": float(total_haber),
            "cuadrado": cuadrado,
        }
