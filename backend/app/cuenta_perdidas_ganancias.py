from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
    q = db.query(JournalLine).join(JournalEntry)
    if date_from is not None:
        q = q.filter(JournalEntry.date >= date_from)
    if date_to is not None:
        q = q.filter(JournalEntry.date <= date_to)
    lines = q.all()

    total_ingresos = Decimal("0")
    total_gastos = Decimal("0")
    for line in lines:
        acct = line.account
        if acct.type == "Ingreso":
            total_ingresos += line.credit - line.debit
        elif acct.type == "Gasto":
            total_gastos += line.debit - line.credit

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
