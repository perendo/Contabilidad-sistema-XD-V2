from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import AuditLog, User

router = APIRouter(tags=["audit"])


def get_audit_log_service(db: Session = Depends(get_db)) -> Session:
    return db


@router.get("/audit-log", response_model=list[dict], status_code=status.HTTP_200_OK)
def list_audit_log(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(AuditLog)
    if company_id is not None:
        query = query.filter(AuditLog.company_id == company_id)
    rows = (
        query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "user_email": r.user_email,
            "action": r.action,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if isinstance(r.created_at, datetime) else r.created_at,
        }
        for r in rows
    ]


@router.put("/audit-log/{audit_id}", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
def put_audit_log(audit_id: int):
    """Los registros de auditoría no se pueden modificar."""
    return None


@router.delete("/audit-log/{audit_id}", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
def delete_audit_log(audit_id: int):
    """Los registros de auditoría no se pueden eliminar."""
    return None
