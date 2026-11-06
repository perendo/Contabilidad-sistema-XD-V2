from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .models import Account, Company, User
from .pgc_seed import seed_pgc

router = APIRouter(prefix="/company", tags=["company"])
companies_router = APIRouter(prefix="/companies", tags=["companies"])


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
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Company:
    if company_id is not None:
        company = db.query(Company).filter(Company.id == company_id).first()
    else:
        company = db.query(Company).first()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no configurada")
    return company


@router.put("", response_model=CompanyOut)
def upsert_company(
    body: CompanyIn,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Company:
    if company_id is not None:
        company = db.query(Company).filter(Company.id == company_id).first()
    else:
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
    # El catalogo contable solo se inicializa la primera vez, no en cada guardado.
    aq = db.query(Account)
    if company_id is not None:
        aq = aq.filter(Account.company_id == company_id)
    if aq.count() == 0:
        seed_pgc(db, company_id=company.id)
    return company


@companies_router.get("", response_model=list[CompanyOut])
def list_companies(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Company]:
    return db.query(Company).order_by(Company.id).all()


@companies_router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    body: CompanyIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Company:
    company = Company(**body.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company
