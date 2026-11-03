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


class IRPFSummaryOut(BaseModel):
    year: int
    quarter: int
    base_sujeta_total: float
    irpf_rate: float | None
    irpf_amount_total: float
    facturas_count: int


@router.get("/irpf-summary", response_model=IRPFSummaryOut, status_code=status.HTTP_200_OK)
def irpf_summary(
    year: int = Query(...),
    quarter: int = Query(ge=1, le=4),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IRPFSummaryOut:
    start_month, end_month = QUARTER_MONTHS[quarter]
    date_from = date(year, start_month, 1)
    date_to = date(year, end_month, 28) if end_month == 2 else date(year, end_month, 30) if end_month in (4, 6, 9, 11) else date(year, end_month, 31)

    q_emitidas = db.query(Invoice).filter(
        Invoice.irpf_rate.isnot(None),
        Invoice.date >= date_from,
        Invoice.date <= date_to,
    )
    q_recibidas = db.query(ReceivedInvoice).filter(
        ReceivedInvoice.irpf_rate.isnot(None),
        ReceivedInvoice.date >= date_from,
        ReceivedInvoice.date <= date_to,
    )

    emitidas = q_emitidas.all()
    recibidas = q_recibidas.all()
    todas = emitidas + recibidas

    base_sujeta_total = sum((inv.base_amount for inv in todas), Decimal("0"))
    irpf_amount_total = sum((inv.irpf_amount or Decimal("0") for inv in todas), Decimal("0"))
    facturas_count = len(todas)

    rates = {inv.irpf_rate for inv in todas if inv.irpf_rate is not None}
    irpf_rate = rates.pop() if len(rates) == 1 else None

    return IRPFSummaryOut(
        year=year,
        quarter=quarter,
        base_sujeta_total=float(base_sujeta_total),
        irpf_rate=float(irpf_rate) if irpf_rate is not None else None,
        irpf_amount_total=float(irpf_amount_total),
        facturas_count=facturas_count,
    )
