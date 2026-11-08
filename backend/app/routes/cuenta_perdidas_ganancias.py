from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.cuenta_perdidas_ganancias import (
    CuentaPerdidasGananciasRepository,
)
from ..schemas.cuenta_perdidas_ganancias import CuentaPerdidasGananciasOut
from ..services.cuenta_perdidas_ganancias import (
    CuentaPerdidasGananciasService,
)

router = APIRouter(tags=["cuenta-perdidas-ganancias"])


def get_cuenta_perdidas_ganancias_service(
    db: Session = Depends(get_db),
) -> CuentaPerdidasGananciasService:
    return CuentaPerdidasGananciasService(CuentaPerdidasGananciasRepository(db))


@router.get(
    "/cuenta-perdidas-ganancias",
    response_model=CuentaPerdidasGananciasOut,
    status_code=status.HTTP_200_OK,
)
def cuenta_perdidas_ganancias(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: CuentaPerdidasGananciasService = Depends(
        get_cuenta_perdidas_ganancias_service
    ),
) -> CuentaPerdidasGananciasOut:
    data = service.compute(company_id, date_from, date_to)
    return CuentaPerdidasGananciasOut(
        date_from=data["date_from"],
        date_to=data["date_to"],
        total_ingresos=data["total_ingresos"],
        total_gastos=data["total_gastos"],
        resultado=data["resultado"],
        tipo_resultado=data["tipo_resultado"],
        grupos=data["grupos"],
        resultado_explotacion=data["resultado_explotacion"],
        resultado_financiero=data["resultado_financiero"],
        resultado_ejercicio=data["resultado_ejercicio"],
    )
