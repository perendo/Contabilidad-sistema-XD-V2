from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.extracto_cuenta import ExtractoCuentaRepository
from ..schemas.extracto_cuenta import (
    ExtractoCuentaOut,
    MovementOut,
)
from ..services.extracto_cuenta import ExtractoCuentaService

router = APIRouter(tags=["extracto-cuenta"])


def get_extracto_cuenta_service(
    db: Session = Depends(get_db),
) -> ExtractoCuentaService:
    return ExtractoCuentaService(ExtractoCuentaRepository(db))


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
    company_id: int | None = Depends(active_company_id_dep),
    service: ExtractoCuentaService = Depends(get_extracto_cuenta_service),
) -> ExtractoCuentaOut:
    data = service.compute(account_id, company_id, date_from, date_to)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no existe"
        )
    return ExtractoCuentaOut(
        account_id=data["account_id"],
        account_code=data["account_code"],
        account_name=data["account_name"],
        date_from=data["date_from"],
        date_to=data["date_to"],
        initial_balance=data["initial_balance"],
        movements=[MovementOut(**m) for m in data["movements"]],
        total_debit=data["total_debit"],
        total_credit=data["total_credit"],
        final_balance=data["final_balance"],
    )
