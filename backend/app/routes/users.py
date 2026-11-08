from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import CompanyMembership, User
from ..repositories.users import UserRepository
from ..schemas.users import UserIn, UserOut
from ..services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("", response_model=list[UserOut])
def list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> list[User]:
    return service.list_users(limit, offset)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserIn,
    current_user: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
) -> User:
    try:
        user = service.create_user(body)
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "ya está registrado" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)
    if company_id is not None:
        membership = CompanyMembership(
            user_id=user.id, company_id=company_id, role="admin"
        )
        db.add(membership)
        db.commit()
    return user
