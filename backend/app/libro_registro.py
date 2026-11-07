from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Invoice, ReceivedInvoice, ThirdParty, User

router = APIRouter(tags=["libro-registro"])


class RegistroFacturaOut(BaseModel):
    date: date
    number: int | None
    supplier_number: str | None
    third_party_id: int
    third_party_tax_id: str
    third_party_name: str
    description: str
    base_amount: float
    vat_rate: float
    vat_amount: float
    irpf_rate: float | None
    irpf_amount: float | None
    total: float


class LibroRegistroOut(BaseModel):
    year: int
    emitidas: list[RegistroFacturaOut]
    recibidas: list[RegistroFacturaOut]
    total_emitidas: float
    total_recibidas: float


@router.get("/libro-registro", response_model=LibroRegistroOut, status_code=status.HTTP_200_OK)
def libro_registro(
    year: int = Query(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> LibroRegistroOut:
    emitidas = db.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.year == year,
    ).all()
    recibidas = (
        db.query(ReceivedInvoice)
        .filter(
            ReceivedInvoice.company_id == company_id,
            ReceivedInvoice.date >= date(year, 1, 1),
            ReceivedInvoice.date <= date(year, 12, 31),
        )
        .all()
    )

    def _factura_a_fila(inv: Invoice) -> RegistroFacturaOut:
        tp = inv.third_party
        return RegistroFacturaOut(
            date=inv.date,
            number=inv.number,
            supplier_number=None,
            third_party_id=tp.id,
            third_party_tax_id=tp.tax_id,
            third_party_name=tp.name,
            description=inv.description,
            base_amount=float(inv.base_amount),
            vat_rate=float(inv.vat_rate),
            vat_amount=float(inv.vat_amount),
            irpf_rate=float(inv.irpf_rate) if inv.irpf_rate is not None else None,
            irpf_amount=float(inv.irpf_amount) if inv.irpf_amount is not None else None,
            total=float(inv.total),
        )

    def _recibida_a_fila(inv: ReceivedInvoice) -> RegistroFacturaOut:
        tp = inv.third_party
        return RegistroFacturaOut(
            date=inv.date,
            number=None,
            supplier_number=inv.supplier_number,
            third_party_id=tp.id,
            third_party_tax_id=tp.tax_id,
            third_party_name=tp.name,
            description=inv.description,
            base_amount=float(inv.base_amount),
            vat_rate=float(inv.vat_rate),
            vat_amount=float(inv.vat_amount),
            irpf_rate=float(inv.irpf_rate) if inv.irpf_rate is not None else None,
            irpf_amount=float(inv.irpf_amount) if inv.irpf_amount is not None else None,
            total=float(inv.total),
        )

    emitidas_rows = [_factura_a_fila(inv) for inv in emitidas]
    recibidas_rows = [_recibida_a_fila(inv) for inv in recibidas]

    total_emitidas = sum((row.total for row in emitidas_rows), 0.0)
    total_recibidas = sum((row.total for row in recibidas_rows), 0.0)

    return LibroRegistroOut(
        year=year,
        emitidas=emitidas_rows,
        recibidas=recibidas_rows,
        total_emitidas=total_emitidas,
        total_recibidas=total_recibidas,
    )
