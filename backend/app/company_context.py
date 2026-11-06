from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import Company


def get_active_company_id(request: Request, db: Session) -> int | None:
    # 1. Header X-Company-Id
    header = request.headers.get("x-company-id")
    if header:
        try:
            return int(header)
        except ValueError:
            pass
    # 2. Cookie active_company_id
    cookie = request.cookies.get("active_company_id")
    if cookie:
        try:
            return int(cookie)
        except ValueError:
            pass
    # 3. Fallback: primera sociedad existente
    company = db.query(Company).order_by(Company.id).first()
    if company is not None:
        return company.id
    return None


def active_company_id_dep(request: Request, db: Session = Depends(get_db)) -> int | None:
    return get_active_company_id(request, db)