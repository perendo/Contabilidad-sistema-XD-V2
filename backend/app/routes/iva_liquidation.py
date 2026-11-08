from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.iva_liquidation import IVALiquidationRepository
from ..schemas.iva_liquidation import IVALiquidationOut
from ..services.iva_liquidation import IVALiquidationService

router = APIRouter(tags=["iva-liquidation"])


def get_iva_liquidation_service(
    db: Session = Depends(get_db),
) -> IVALiquidationService:
    return IVALiquidationService(IVALiquidationRepository(db))


@router.get(
    "/iva-liquidation",
    response_model=IVALiquidationOut,
    status_code=status.HTTP_200_OK,
)
def iva_liquidation(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: IVALiquidationService = Depends(get_iva_liquidation_service),
) -> IVALiquidationOut:
    data = service.compute(date_from, date_to, company_id)
    return IVALiquidationOut(
        date_from=data["date_from"],
        date_to=data["date_to"],
        iva_devengado=data["iva_devengado"],
        iva_deducible=data["iva_deducible"],
        saldo=data["saldo"],
        tipo_saldo=data["tipo_saldo"],
        breakdown=data["breakdown"],
    )
