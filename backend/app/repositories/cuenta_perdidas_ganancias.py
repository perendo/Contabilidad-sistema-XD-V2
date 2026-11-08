from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Account, JournalEntry, JournalLine


class CuentaPerdidasGananciasRepository:
    def __init__(self, db: Session):
        self.db = db

    def compute(self, company_id, date_from: date | None, date_to: date | None):
        rows = (
            self.db.query(
                Account.type,
                func.coalesce(func.sum(JournalLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalLine.credit), 0).label("total_credit"),
            )
            .join(JournalLine, Account.id == JournalLine.account_id)
            .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
            .filter(JournalEntry.status == "accepted")
            .filter(Account.type.in_(("Ingreso", "Gasto")))
        )
        if company_id is not None:
            rows = rows.filter(
                JournalEntry.company_id == company_id,
                Account.company_id == company_id,
            )
        if date_from is not None:
            rows = rows.filter(JournalEntry.date >= date_from)
        if date_to is not None:
            rows = rows.filter(JournalEntry.date <= date_to)

        grouped = rows.group_by(Account.type).all()

        total_ingresos = Decimal("0")
        total_gastos = Decimal("0")
        for account_type, total_debit, total_credit in grouped:
            debit = Decimal(str(total_debit))
            credit = Decimal(str(total_credit))
            if account_type == "Ingreso":
                total_ingresos += credit - debit
            elif account_type == "Gasto":
                total_gastos += debit - credit

        resultado = total_ingresos - total_gastos
        if resultado > 0:
            tipo_resultado = "beneficio"
        elif resultado < 0:
            tipo_resultado = "pérdida"
        else:
            tipo_resultado = "neutro"

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_ingresos": float(total_ingresos),
            "total_gastos": float(total_gastos),
            "resultado": float(resultado),
            "tipo_resultado": tipo_resultado,
        }
