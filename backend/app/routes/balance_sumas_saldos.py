from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.balance_sumas_saldos import BalanceSumasSaldosRepository
from ..schemas.balance_sumas_saldos import (
    BalanceAccountOut,
    BalanceSumasSaldosOut,
)
from ..services.balance_sumas_saldos import BalanceSumasSaldosService

router = APIRouter(tags=["balance-sumas-saldos"])


def get_balance_sumas_saldos_service(
    db: Session = Depends(get_db),
) -> BalanceSumasSaldosService:
    return BalanceSumasSaldosService(BalanceSumasSaldosRepository(db))


@router.get(
    "/balance-sumas-saldos",
    response_model=BalanceSumasSaldosOut,
    status_code=status.HTTP_200_OK,
)
def balance_sumas_saldos(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: BalanceSumasSaldosService = Depends(get_balance_sumas_saldos_service),
) -> BalanceSumasSaldosOut:
    data = service.compute(company_id, date_from, date_to)
    return BalanceSumasSaldosOut(
        date_from=data["date_from"],
        date_to=data["date_to"],
        accounts=[BalanceAccountOut(**a) for a in data["accounts"]],
        total_debe=data["total_debe"],
        total_haber=data["total_haber"],
        cuadrado=data["cuadrado"],
    )
