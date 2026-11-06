from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Account, ThirdParty, User

router = APIRouter(tags=["third-parties"])

ALLOWED_TYPES = {"cliente", "proveedor", "Cliente", "Proveedor"}


class ThirdPartyIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(min_length=1, max_length=255, validation_alias=AliasChoices("name", "nombre", "razon_social"))
    tax_id: str = Field(min_length=1, max_length=50, validation_alias=AliasChoices("tax_id", "nif", "cif", "nif_cif"))
    type: str = Field(validation_alias=AliasChoices("type", "tipo"))
    account_id: int = Field(validation_alias=AliasChoices("account_id", "accountId", "cuenta_id", "subcuenta_id"))
    address: str = Field(default="", max_length=500, validation_alias=AliasChoices("address", "domicilio", "direccion"))
    phone: str = Field(default="", max_length=50, validation_alias=AliasChoices("phone", "telefono"))
    email: str = Field(default="", max_length=255, validation_alias=AliasChoices("email", "correo"))


class ThirdPartyOut(ThirdPartyIn):
    id: int
    type: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


def _normalize_type(value: str) -> str:
    low = value.strip().lower()
    if low in ("cliente",):
        return "Cliente"
    if low in ("proveedor",):
        return "Proveedor"
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de tercero no válido")


@router.post("/third-parties", response_model=ThirdPartyOut, status_code=status.HTTP_201_CREATED)
@router.post("/terceros", response_model=ThirdPartyOut, status_code=status.HTTP_201_CREATED)
def create_third_party(
    body: ThirdPartyIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> ThirdParty:
    if body.type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de tercero no válido")
    aq = db.query(Account).filter(Account.id == body.account_id)
    if company_id is not None:
        aq = aq.filter(Account.company_id == company_id)
    account = aq.first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subcuenta no existe")
    normalized = _normalize_type(body.type)
    tp = ThirdParty(
        account_id=body.account_id,
        name=body.name,
        tax_id=body.tax_id,
        type=normalized,
        address=body.address,
        phone=body.phone,
        email=body.email,
        company_id=company_id,
    )
    db.add(tp)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se pudo crear el tercero")
    db.refresh(tp)
    return tp


@router.get("/third-parties", response_model=list[ThirdPartyOut])
@router.get("/terceros", response_model=list[ThirdPartyOut])
def list_third_parties(
    type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> list[ThirdParty]:
    q = db.query(ThirdParty)
    if company_id is not None:
        q = q.filter(ThirdParty.company_id == company_id)
    if type is not None:
        try:
            norm = _normalize_type(type)
        except HTTPException:
            norm = type
        q = q.filter(ThirdParty.type == norm)
    if search:
        like = f"%{search}%"
        q = q.filter((ThirdParty.name.ilike(like)) | (ThirdParty.tax_id.ilike(like)))
    return q.order_by(ThirdParty.id).all()