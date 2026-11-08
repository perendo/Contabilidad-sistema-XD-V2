from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import case, extract, func
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
    total_q1: float
    total_q2: float
    total_q3: float
    total_q4: float
    total_annual: float


class Modelo347Out(BaseModel):
    year: int
    threshold: float
    third_parties: list[ThirdPartySummaryOut]


def _mes_expr(model):
    return extract("month", model.date)


def _totals_query(
    db: Session,
    model,
    company_id: int | None,
    date_from: date,
    date_to: date,
):
    mes = _mes_expr(model)
    return (
        db.query(
            model.third_party_id.label("third_party_id"),
            func.sum(case((mes.in_([1, 2, 3]), model.total), else_=0)).label(
                "total_q1"
            ),
            func.sum(case((mes.in_([4, 5, 6]), model.total), else_=0)).label(
                "total_q2"
            ),
            func.sum(case((mes.in_([7, 8, 9]), model.total), else_=0)).label(
                "total_q3"
            ),
            func.sum(case((mes.in_([10, 11, 12]), model.total), else_=0)).label(
                "total_q4"
            ),
            func.sum(model.total).label("total_annual"),
        )
        .filter(
            model.company_id == company_id,
            model.date >= date_from,
            model.date <= date_to,
            model.irpf_rate.is_(None),
            model.irpf_amount.is_(None),
        )
        .group_by(model.third_party_id)
    )


def compute_modelo_347(
    db: Session,
    year: int,
    threshold: float,
    company_id: int | None = None,
) -> dict:
    date_from = date(year, 1, 1)
    date_to = date(year, 12, 31)
    totals = _totals_query(
        db, Invoice, company_id, date_from, date_to
    ).union_all(
        _totals_query(db, ReceivedInvoice, company_id, date_from, date_to)
    ).subquery()

    rows = (
        db.query(
            ThirdParty.id,
            ThirdParty.tax_id,
            ThirdParty.name,
            func.sum(totals.c.total_q1).label("total_q1"),
            func.sum(totals.c.total_q2).label("total_q2"),
            func.sum(totals.c.total_q3).label("total_q3"),
            func.sum(totals.c.total_q4).label("total_q4"),
            func.sum(totals.c.total_annual).label("total_annual"),
        )
        .join(totals, totals.c.third_party_id == ThirdParty.id)
        .filter(ThirdParty.company_id == company_id)
        .group_by(ThirdParty.id, ThirdParty.tax_id, ThirdParty.name)
        .having(func.sum(totals.c.total_annual) > Decimal(str(threshold)))
        .order_by(ThirdParty.tax_id)
        .all()
    )

    return {
        "year": year,
        "threshold": threshold,
        "third_parties": [
            {
                "third_party_id": third_party_id,
                "tax_id": tax_id,
                "name": name,
                "total_q1": float(total_q1),
                "total_q2": float(total_q2),
                "total_q3": float(total_q3),
                "total_q4": float(total_q4),
                "total_annual": float(total_annual),
            }
            for third_party_id, tax_id, name, total_q1, total_q2, total_q3, total_q4, total_annual in rows
        ],
    }


@router.get("/modelo-347", response_model=Modelo347Out, status_code=status.HTTP_200_OK)
def modelo_347(
    year: int = Query(...),
    threshold: float = Query(ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Modelo347Out:
    data = compute_modelo_347(db, year, threshold, company_id)
    return Modelo347Out(
        year=data["year"],
        threshold=data["threshold"],
        third_parties=[
            ThirdPartySummaryOut(**item) for item in data["third_parties"]
        ],
    )
