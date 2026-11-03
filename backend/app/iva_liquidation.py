from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
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


def _vat_by_rate(invoices: list, rate: Decimal) -> Decimal:
    return sum((inv.vat_amount for inv in invoices if inv.vat_rate == rate), Decimal("0"))


@router.get("/iva-liquidation", response_model=IVALiquidationOut, status_code=status.HTTP_200_OK)
def iva_liquidation(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IVALiquidationOut:
    q_emitidas = db.query(Invoice)
    q_recibidas = db.query(ReceivedInvoice)
    if date_from is not None:
        q_emitidas = q_emitidas.filter(Invoice.date >= date_from)
        q_recibidas = q_recibidas.filter(ReceivedInvoice.date >= date_from)
    if date_to is not None:
        q_emitidas = q_emitidas.filter(Invoice.date <= date_to)
        q_recibidas = q_recibidas.filter(ReceivedInvoice.date <= date_to)

    emitidas = q_emitidas.all()
    recibidas = q_recibidas.all()
    iva_devengado = sum((inv.vat_amount for inv in emitidas), Decimal("0"))
    iva_deducible = sum((inv.vat_amount for inv in recibidas), Decimal("0"))
    saldo = iva_devengado - iva_deducible
    if saldo > 0:
        tipo_saldo = "a ingresar"
    elif saldo < 0:
        tipo_saldo = "a compensar"
    else:
        tipo_saldo = "neutro"

    breakdown: dict[str, IVARateBreakdown] = {}
    for rate in VAT_RATES:
        breakdown[str(rate)] = IVARateBreakdown(
            devengado=float(_vat_by_rate(emitidas, rate)),
            deducible=float(_vat_by_rate(recibidas, rate)),
        )

    return IVALiquidationOut(
        date_from=date_from,
        date_to=date_to,
        iva_devengado=float(iva_devengado),
        iva_deducible=float(iva_deducible),
        saldo=float(saldo),
        tipo_saldo=tipo_saldo,
        breakdown=breakdown,
    )
