from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
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
) -> BalanceSumasSaldosOut:
    q = db.query(JournalLine).join(JournalEntry)
    if date_from is not None:
        q = q.filter(JournalEntry.date >= date_from)
    if date_to is not None:
        q = q.filter(JournalEntry.date <= date_to)
    lines = q.all()

    accounts: dict[int, dict] = {}
    for line in lines:
        acct = line.account
        if acct.id not in accounts:
            accounts[acct.id] = {
                "code": acct.code,
                "name": acct.name,
                "debe": Decimal("0"),
                "haber": Decimal("0"),
            }
        accounts[acct.id]["debe"] += line.debit
        accounts[acct.id]["haber"] += line.credit

    total_debe = Decimal("0")
    total_haber = Decimal("0")
    rows: list[BalanceAccountOut] = []
    for acct_id in sorted(accounts.keys(), key=lambda aid: accounts[aid]["code"]):
        acc = accounts[acct_id]
        debe = acc["debe"]
        haber = acc["haber"]
        saldo = debe - haber
        total_debe += debe
        total_haber += haber
        rows.append(
            BalanceAccountOut(
                code=acc["code"],
                name=acc["name"],
                debe=float(debe),
                haber=float(haber),
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
