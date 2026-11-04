from sqlalchemy import or_
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Invoice, ReceivedInvoice, User

router = APIRouter(tags=["irpf-summary"])

QUARTER_MONTHS = {
    1: (1, 3),
    2: (4, 6),
    3: (7, 9),
    4: (10, 12),
}


class Modelo111Summary(BaseModel):
    base: float
    retenciones_a_ingresar: float


class PagosACuenta130Summary(BaseModel):
    base: float
    retenciones_soportadas: float


class IRPFSummaryOut(BaseModel):
    year: int
    quarter: int
    modelo_111: Modelo111Summary
    pagos_a_cuenta_130: PagosACuenta130Summary
    facturas_emitidas_count: int
    facturas_recibidas_count: int


@router.get("/irpf-summary", response_model=IRPFSummaryOut, status_code=status.HTTP_200_OK)
def irpf_summary(
    year: int = Query(...),
    quarter: int = Query(ge=1, le=4),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IRPFSummaryOut:
    start_month, end_month = QUARTER_MONTHS[quarter]
    date_from = date(year, start_month, 1)
    if end_month == 2:
        date_to = date(year, end_month, 28)
    elif end_month in (4, 6, 9, 11):
        date_to = date(year, end_month, 30)
    else:
        date_to = date(year, end_month, 31)

    q_emitidas = db.query(Invoice).filter(
        or_(Invoice.irpf_rate.isnot(None), Invoice.irpf_amount > 0),
        Invoice.date >= date_from,
        Invoice.date <= date_to,
    )
    q_recibidas = db.query(ReceivedInvoice).filter(
        or_(ReceivedInvoice.irpf_rate.isnot(None), ReceivedInvoice.irpf_amount > 0),
        ReceivedInvoice.date >= date_from,
        ReceivedInvoice.date <= date_to,
    )

    emitidas = q_emitidas.all()
    recibidas = q_recibidas.all()

    # Retenciones practicadas a proveedores/profesionales (a ingresar -> Modelo 111/115)
    base_recibidas = sum((inv.base_amount for inv in recibidas), Decimal("0"))
    retenciones_practicadas = sum(
        (inv.irpf_amount or Decimal("0") for inv in recibidas), Decimal("0")
    )

    # Retenciones soportadas por clientes (pagos a cuenta -> Modelo 130/200)
    base_emitidas = sum((inv.base_amount for inv in emitidas), Decimal("0"))
    retenciones_soportadas = sum(
        (inv.irpf_amount or Decimal("0") for inv in emitidas), Decimal("0")
    )

    return IRPFSummaryOut(
        year=year,
        quarter=quarter,
        modelo_111=Modelo111Summary(
            base=float(base_recibidas),
            retenciones_a_ingresar=float(retenciones_practicadas),
        ),
        pagos_a_cuenta_130=PagosACuenta130Summary(
            base=float(base_emitidas),
            retenciones_soportadas=float(retenciones_soportadas),
        ),
        facturas_emitidas_count=len(emitidas),
        facturas_recibidas_count=len(recibidas),
    )
