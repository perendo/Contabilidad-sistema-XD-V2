from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sqlalchemy import func

from .auth import get_current_user
from .database import get_db
from .models import Account, JournalEntry, JournalLine, User

router = APIRouter(tags=["cuenta-perdidas-ganancias"])


class CuentaPerdidasGananciasOut(BaseModel):
    date_from: date | None
    date_to: date | None
    total_ingresos: float
    total_gastos: float
    resultado: float
    tipo_resultado: str


@router.get(
    "/cuenta-perdidas-ganancias",
    response_model=CuentaPerdidasGananciasOut,
    status_code=status.HTTP_200_OK,
)
def cuenta_perdidas_ganancias(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CuentaPerdidasGananciasOut:
    rows = (
        db.query(
            Account.type,
            func.coalesce(func.sum(JournalLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("total_credit"),
        )
        .join(JournalLine, Account.id == JournalLine.account_id)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .filter(JournalEntry.status == "accepted")
        .filter(Account.type.in_(("Ingreso", "Gasto")))
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

    return CuentaPerdidasGananciasOut(
        date_from=date_from,
        date_to=date_to,
        total_ingresos=float(total_ingresos),
        total_gastos=float(total_gastos),
        resultado=float(resultado),
        tipo_resultado=tipo_resultado,
    )
