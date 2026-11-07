import calendar
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
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


def _quarter_dates(year: int, quarter: int) -> tuple[date, date]:
    start_month, end_month = QUARTER_MONTHS[quarter]
    date_from = date(year, start_month, 1)
    if end_month == 2:
        date_to = date(year, end_month, calendar.monthrange(year, end_month)[1])
    elif end_month in (4, 6, 9, 11):
        date_to = date(year, end_month, 30)
    else:
        date_to = date(year, end_month, 31)
    return date_from, date_to


def _irpf_totals(
    db: Session,
    model,
    company_id: int | None,
    date_from: date,
    date_to: date,
) -> tuple[Decimal, Decimal, int]:
    base, retention, count = (
        db.query(
            func.coalesce(func.sum(model.base_amount), 0),
            func.coalesce(func.sum(model.irpf_amount), 0),
            func.count(model.id),
        )
        .filter(
            model.company_id == company_id,
            or_(model.irpf_rate.isnot(None), model.irpf_amount > 0),
            model.date >= date_from,
            model.date <= date_to,
        )
        .one()
    )
    return Decimal(str(base)), Decimal(str(retention)), int(count)


def compute_irpf(
    db: Session,
    year: int,
    quarter: int,
    company_id: int | None = None,
) -> dict:
    date_from, date_to = _quarter_dates(year, quarter)
    base_recibidas, retenciones_practicadas, count_recibidas = _irpf_totals(
        db, ReceivedInvoice, company_id, date_from, date_to
    )
    base_emitidas, retenciones_soportadas, count_emitidas = _irpf_totals(
        db, Invoice, company_id, date_from, date_to
    )

    return {
        "year": year,
        "quarter": quarter,
        "date_from": date_from,
        "date_to": date_to,
        "modelo_111": {
            "base": float(base_recibidas),
            "retenciones_a_ingresar": float(retenciones_practicadas),
        },
        "pagos_a_cuenta_130": {
            "base": float(base_emitidas),
            "retenciones_soportadas": float(retenciones_soportadas),
        },
        "facturas_emitidas_count": count_emitidas,
        "facturas_recibidas_count": count_recibidas,
    }


@router.get("/irpf-summary", response_model=IRPFSummaryOut, status_code=status.HTTP_200_OK)
def irpf_summary(
    year: int = Query(...),
    quarter: int = Query(ge=1, le=4),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> IRPFSummaryOut:
    data = compute_irpf(db, year, quarter, company_id)
    return IRPFSummaryOut(
        year=data["year"],
        quarter=data["quarter"],
        modelo_111=Modelo111Summary(**data["modelo_111"]),
        pagos_a_cuenta_130=PagosACuenta130Summary(**data["pagos_a_cuenta_130"]),
        facturas_emitidas_count=data["facturas_emitidas_count"],
        facturas_recibidas_count=data["facturas_recibidas_count"],
    )
