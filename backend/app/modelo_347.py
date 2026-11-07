from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Invoice, ReceivedInvoice, ThirdParty, User

router = APIRouter(tags=["modelo-347"])


class ThirdPartySummaryOut(BaseModel):
    third_party_id: int
    tax_id: str
    name: str
    total_annual: float


class Modelo347Out(BaseModel):
    year: int
    threshold: float
    third_parties: list[ThirdPartySummaryOut]


@router.get("/modelo-347", response_model=Modelo347Out, status_code=status.HTTP_200_OK)
def modelo_347(
    year: int = Query(...),
    threshold: float = Query(ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Modelo347Out:
    emitidas = db.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.year == year,
    ).all()
    recibidas = db.query(ReceivedInvoice).filter(
        ReceivedInvoice.company_id == company_id,
        ReceivedInvoice.date >= date(year, 1, 1),
        ReceivedInvoice.date <= date(year, 12, 31),
    ).all()

    totals: dict[int, Decimal] = {}
    for inv in emitidas:
        totals[inv.third_party_id] = totals.get(inv.third_party_id, Decimal("0")) + inv.total
    for inv in recibidas:
        totals[inv.third_party_id] = totals.get(inv.third_party_id, Decimal("0")) + inv.total

    threshold_decimal = Decimal(str(threshold))
    third_party_ids = [tp_id for tp_id, total in totals.items() if total > threshold_decimal]
    third_parties = (
        db.query(ThirdParty).filter(
            ThirdParty.id.in_(third_party_ids),
            ThirdParty.company_id == company_id,
        ).all()
        if third_party_ids
        else []
    )

    result: list[ThirdPartySummaryOut] = []
    for tp in third_parties:
        result.append(
            ThirdPartySummaryOut(
                third_party_id=tp.id,
                tax_id=tp.tax_id,
                name=tp.name,
                total_annual=float(totals[tp.id]),
            )
        )

    return Modelo347Out(
        year=year,
        threshold=threshold,
        third_parties=result,
    )
