from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Invoice, ReceivedInvoice, User

router = APIRouter(tags=["iva-liquidation"])


class IVARateBreakdown(BaseModel):
    devengado: float
    deducible: float


class IVALiquidationOut(BaseModel):
    date_from: date | None
    date_to: date | None
    iva_devengado: float
    iva_deducible: float
    saldo: float
    tipo_saldo: str
    breakdown: dict[str, IVARateBreakdown]


VAT_RATES = [Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0")]


def _vat_totals(
    db: Session,
    model,
    company_id: int | None,
    date_from: date | None,
    date_to: date | None,
) -> dict[Decimal, Decimal]:
    q = db.query(
        model.vat_rate,
        func.coalesce(func.sum(model.vat_amount), 0),
    ).filter(model.company_id == company_id)
    if date_from is not None:
        q = q.filter(model.date >= date_from)
    if date_to is not None:
        q = q.filter(model.date <= date_to)

    return {
        Decimal(str(rate)): Decimal(str(total))
        for rate, total in q.group_by(model.vat_rate).all()
    }


def compute_iva(
    db: Session,
    date_from: date | None,
    date_to: date | None,
    company_id: int | None = None,
) -> dict:
    emitidas = _vat_totals(db, Invoice, company_id, date_from, date_to)
    recibidas = _vat_totals(db, ReceivedInvoice, company_id, date_from, date_to)
    iva_devengado = sum(emitidas.values(), Decimal("0"))
    iva_deducible = sum(recibidas.values(), Decimal("0"))
    saldo = iva_devengado - iva_deducible
    if saldo > 0:
        tipo_saldo = "a ingresar"
    elif saldo < 0:
        tipo_saldo = "a compensar"
    else:
        tipo_saldo = "neutro"

    breakdown = {
        str(rate): {
            "devengado": float(emitidas.get(rate, Decimal("0"))),
            "deducible": float(recibidas.get(rate, Decimal("0"))),
        }
        for rate in VAT_RATES
    }

    return {
        "date_from": date_from,
        "date_to": date_to,
        "iva_devengado": float(iva_devengado),
        "iva_deducible": float(iva_deducible),
        "saldo": float(saldo),
        "tipo_saldo": tipo_saldo,
        "breakdown": breakdown,
    }


@router.get("/iva-liquidation", response_model=IVALiquidationOut, status_code=status.HTTP_200_OK)
def iva_liquidation(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> IVALiquidationOut:
    data = compute_iva(db, date_from, date_to, company_id)
    return IVALiquidationOut(
        date_from=data["date_from"],
        date_to=data["date_to"],
        iva_devengado=data["iva_devengado"],
        iva_deducible=data["iva_deducible"],
        saldo=data["saldo"],
        tipo_saldo=data["tipo_saldo"],
        breakdown=data["breakdown"],
    )
