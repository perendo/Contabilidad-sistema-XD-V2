from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import Account, User
from ..repositories.accounts import AccountRepository
from ..schemas.accounts import AccountIn, AccountOut
from ..services.accounts import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(AccountRepository(db))


@router.post(
    "", response_model=AccountOut, status_code=status.HTTP_201_CREATED
)
def create_account(
    body: AccountIn,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: AccountService = Depends(get_account_service),
) -> Account:
    try:
        return service.create_account(body, company_id)
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "duplicado" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)


@router.get("", response_model=list[AccountOut])
def list_accounts(
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: AccountService = Depends(get_account_service),
) -> list[Account]:
    return service.list_accounts(company_id, search, limit, offset)
