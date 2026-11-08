from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import ThirdParty, User
from ..repositories.third_parties import ThirdPartyRepository
from ..schemas.third_parties import ThirdPartyIn, ThirdPartyOut
from ..services.third_parties import ThirdPartyService

router = APIRouter(tags=["third-parties"])


def get_third_party_service(db: Session = Depends(get_db)) -> ThirdPartyService:
    return ThirdPartyService(ThirdPartyRepository(db))


@router.post(
    "/third-parties",
    response_model=ThirdPartyOut,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/terceros",
    response_model=ThirdPartyOut,
    status_code=status.HTTP_201_CREATED,
)
def create_third_party(
    body: ThirdPartyIn,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: ThirdPartyService = Depends(get_third_party_service),
) -> ThirdParty:
    try:
        return service.create_third_party(body, company_id)
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "No se pudo crear" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)


@router.get("/third-parties", response_model=list[ThirdPartyOut])
@router.get("/terceros", response_model=list[ThirdPartyOut])
def list_third_parties(
    type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: ThirdPartyService = Depends(get_third_party_service),
) -> list[ThirdParty]:
    try:
        norm = _normalize_type_query(type)
    except ValueError:
        norm = type
    return service.list_third_parties(company_id, norm, search)


def _normalize_type_query(value: str | None) -> str | None:
    if value is None:
        return None
    from ..schemas.third_parties import _normalize_type

    return _normalize_type(value)
