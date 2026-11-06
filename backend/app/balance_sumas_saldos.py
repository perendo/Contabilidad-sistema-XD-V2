from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sqlalchemy import func

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Account, JournalEntry, JournalLine, User

router = APIRouter(tags=["balance-sumas-saldos"])


class BalanceAccountOut(BaseModel):
    code: str
    name: str
    debe: float
    haber: float
    saldo: float


class BalanceSumasSaldosOut(BaseModel):
    date_from: date | None
    date_to: date | None
    accounts: list[BalanceAccountOut]
    total_debe: float
    total_haber: float
    cuadrado: bool


@router.get(
    "/balance-sumas-saldos",
    response_model=BalanceSumasSaldosOut,
    status_code=status.HTTP_200_OK,
)
def balance_sumas_saldos(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> BalanceSumasSaldosOut:
    stmt = (
        db.query(
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
        stmt = stmt.filter(JournalEntry.company_id == company_id, Account.company_id == company_id)
    if date_from is not None:
        stmt = stmt.filter(JournalEntry.date >= date_from)
    if date_to is not None:
        stmt = stmt.filter(JournalEntry.date <= date_to)

    rows_db = stmt.group_by(Account.id, Account.code, Account.name).order_by(Account.code).all()

    total_debe = Decimal("0")
    total_haber = Decimal("0")
    rows: list[BalanceAccountOut] = []
    for code, name, debe, haber in rows_db:
        debe_dec = Decimal(str(debe))
        haber_dec = Decimal(str(haber))
        saldo = debe_dec - haber_dec
        total_debe += debe_dec
        total_haber += haber_dec
        rows.append(
            BalanceAccountOut(
                code=code,
                name=name,
                debe=float(debe_dec),
                haber=float(haber_dec),
                saldo=float(saldo),
            )
        )

    cuadrado = total_debe == total_haber

    return BalanceSumasSaldosOut(
        date_from=date_from,
        date_to=date_to,
        accounts=rows,
        total_debe=float(total_debe),
        total_haber=float(total_haber),
        cuadrado=cuadrado,
    )
