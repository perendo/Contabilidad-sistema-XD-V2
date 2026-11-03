from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Account, JournalEntry, JournalLine, User

router = APIRouter(tags=["extracto-cuenta"])


class MovementOut(BaseModel):
    date: date
    entry_id: int
    entry_description: str
    description: str
    debit: float
    credit: float
    running_balance: float


class ExtractoCuentaOut(BaseModel):
    account_id: int
    account_code: str
    account_name: str
    date_from: date | None
    date_to: date | None
    movements: list[MovementOut]
    total_debit: float
    total_credit: float
    final_balance: float


@router.get(
    "/extracto-cuenta",
    response_model=ExtractoCuentaOut,
    status_code=status.HTTP_200_OK,
)
def extracto_cuenta(
    account_id: int = Query(...),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractoCuentaOut:
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no existe")

    q = db.query(JournalLine).join(JournalEntry).filter(JournalLine.account_id == account_id)
    if date_from is not None:
        q = q.filter(JournalEntry.date >= date_from)
    if date_to is not None:
        q = q.filter(JournalEntry.date <= date_to)
    lines = q.order_by(JournalEntry.date, JournalEntry.id).all()

    movements: list[MovementOut] = []
    running = Decimal("0")
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line in lines:
        entry = line.entry
        debit = line.debit
        credit = line.credit
        running += debit - credit
        total_debit += debit
        total_credit += credit
        movements.append(
            MovementOut(
                date=entry.date,
                entry_id=entry.id,
                entry_description=entry.description,
                description=line.description,
                debit=float(debit),
                credit=float(credit),
                running_balance=float(running),
            )
        )

    return ExtractoCuentaOut(
        account_id=account.id,
        account_code=account.code,
        account_name=account.name,
        date_from=date_from,
        date_to=date_to,
        movements=movements,
        total_debit=float(total_debit),
        total_credit=float(total_credit),
        final_balance=float(running),
    )
