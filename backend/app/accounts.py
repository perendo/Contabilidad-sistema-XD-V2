import re
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Account, User

router = APIRouter(prefix="/accounts", tags=["accounts"])

ACCOUNT_TYPES = {"Activo", "Pasivo", "Patrimonio Neto", "Ingreso", "Gasto"}


class AccountIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    type: str
    level: int = Field(ge=1, le=8)
    is_detail: bool = False
    parent_id: int | None = None


class AccountOut(AccountIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


def _escape_like(value: str) -> str:
    return re.sub(r"([%_])", r"\\\1", value)


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    body: AccountIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Account:
    if body.type not in ACCOUNT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de cuenta no válido")
    if body.parent_id is None:
        if body.level != 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Las cuentas de nivel 1 no tienen padre")
    else:
        parent = db.query(Account).filter(Account.id == body.parent_id, Account.company_id == company_id).first()
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuenta padre no existe")
        if body.level != parent.level + 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nivel debe ser nivel del padre + 1")
        if not body.code.startswith(parent.code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código debe comenzar por el código del padre")
        if body.level > 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nivel máximo 8")
    account = Account(**body.model_dump(), company_id=company_id)
    db.add(account)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de cuenta duplicado")
    db.refresh(account)
    return account


@router.get("", response_model=list[AccountOut])
def list_accounts(
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> list[Account]:
    q = db.query(Account).filter(Account.company_id == company_id)
    if search:
        escaped = _escape_like(search)
        like = f"%{escaped}%"
        q = q.filter((Account.code.ilike(like, escape="\\")) | (Account.name.ilike(like, escape="\\")))
    return q.order_by(Account.code).offset(offset).limit(limit).all()
