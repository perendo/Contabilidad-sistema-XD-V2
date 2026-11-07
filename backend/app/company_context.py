from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Company, CompanyMembership


def get_active_company_id(
    request: Request, db: Session, current_user
) -> int | None:
    # 1. Header X-Company-Id
    header = request.headers.get("x-company-id")
    # 2. Cookie active_company_id
    cookie = request.cookies.get("active_company_id")

    candidate = None
    if header:
        try:
            candidate = int(header)
        except ValueError:
            pass
    if candidate is None and cookie:
        try:
            candidate = int(cookie)
        except ValueError:
            pass

    if candidate is None:
        # Fallback: primera sociedad a la que el usuario pertenece
        membership = (
            db.query(CompanyMembership)
            .filter(CompanyMembership.user_id == current_user.id)
            .order_by(CompanyMembership.id)
            .first()
        )
        if membership is not None:
            return membership.company_id
        # Último recurso: primera sociedad existente (solo si no hay membresías)
        company = db.query(Company).order_by(Company.id).first()
        if company is not None:
            return company.id
        return None

    # Validar que el usuario sea miembro de la empresa solicitada
    membership = (
        db.query(CompanyMembership)
        .filter(
            CompanyMembership.user_id == current_user.id,
            CompanyMembership.company_id == candidate,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta empresa",
        )
    return candidate


def active_company_id_dep(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int | None:
    return get_active_company_id(request, db, current_user)
