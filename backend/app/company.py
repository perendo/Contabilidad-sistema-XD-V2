from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Company
from .pgc_seed import seed_pgc

router = APIRouter(prefix="/company", tags=["company"])


class CompanyIn(BaseModel):
    name: str
    tax_id: str
    address: str
    fiscal_year: str


class CompanyOut(CompanyIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=CompanyOut)
def get_company(
    _: str = Depends(get_current_user), db: Session = Depends(get_db)
) -> Company:
    company = db.query(Company).first()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no configurada")
    return company


@router.put("", response_model=CompanyOut)
def upsert_company(
    body: CompanyIn,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Company:
    company = db.query(Company).first()
    if company is None:
        company = Company(**body.model_dump())
        db.add(company)
    else:
        company.name = body.name
        company.tax_id = body.tax_id
        company.address = body.address
        company.fiscal_year = body.fiscal_year
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al guardar la empresa")
    db.refresh(company)
    seed_pgc(db)
    return company
