from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.irpf_summary import IRPFSummaryRepository
from ..schemas.irpf_summary import (
    IRPFSummaryOut,
    Modelo111Summary,
    PagosACuenta130Summary,
)
from ..services.irpf_summary import IRPFSummaryService

router = APIRouter(tags=["irpf-summary"])


def get_irpf_summary_service(
    db: Session = Depends(get_db),
) -> IRPFSummaryService:
    return IRPFSummaryService(IRPFSummaryRepository(db))


@router.get(
    "/irpf-summary",
    response_model=IRPFSummaryOut,
    status_code=status.HTTP_200_OK,
)
def irpf_summary(
    year: int = Query(...),
    quarter: int = Query(ge=1, le=4),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: IRPFSummaryService = Depends(get_irpf_summary_service),
) -> IRPFSummaryOut:
    data = service.compute(year, quarter, company_id)
    return IRPFSummaryOut(
        year=data["year"],
        quarter=data["quarter"],
        modelo_111=Modelo111Summary(**data["modelo_111"]),
        pagos_a_cuenta_130=PagosACuenta130Summary(**data["pagos_a_cuenta_130"]),
        facturas_emitidas_count=data["facturas_emitidas_count"],
        facturas_recibidas_count=data["facturas_recibidas_count"],
    )
