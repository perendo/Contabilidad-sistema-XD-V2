from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import Company, User
from ..repositories.company import (
    CompanyMembershipRepository,
    CompanyRepository,
)
from ..schemas.company import CompanyIn, CompanyOut
from ..services.company import CompanyService

router = APIRouter(prefix="/company", tags=["company"])
companies_router = APIRouter(prefix="/companies", tags=["companies"])


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    return CompanyService(
        CompanyRepository(db), CompanyMembershipRepository(db)
    )


@router.get("", response_model=CompanyOut)
def get_company(
    _: str = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: CompanyService = Depends(get_company_service),
) -> Company:
    if company_id is not None:
        company = service.company_repo.get_by_id(company_id)
    else:
        company = service.company_repo.get_any()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no configurada",
        )
    return company


@router.put("", response_model=CompanyOut)
def upsert_company(
    body: CompanyIn,
    current_user: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: CompanyService = Depends(get_company_service),
) -> Company:
    try:
        return service.upsert_company(body, current_user.id, company_id)
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "Conflicto" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)


@companies_router.get("", response_model=list[CompanyOut])
def list_companies(
    current_user: User = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> list[Company]:
    return service.list_companies(current_user.id)


@companies_router.post(
    "", response_model=CompanyOut, status_code=status.HTTP_201_CREATED
)
def create_company(
    body: CompanyIn,
    current_user: User = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> Company:
    return service.create_company(body, current_user.id)
