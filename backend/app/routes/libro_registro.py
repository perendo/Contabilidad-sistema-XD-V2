from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.libro_registro import LibroRegistroRepository
from ..schemas.libro_registro import (
    LibroRegistroOut,
    RegistroFacturaOut,
)
from ..services.libro_registro import LibroRegistroService

router = APIRouter(tags=["libro-registro"])


def get_libro_registro_service(
    db: Session = Depends(get_db),
) -> LibroRegistroService:
    return LibroRegistroService(LibroRegistroRepository(db))


@router.get("/libro-registro", response_model=LibroRegistroOut, status_code=status.HTTP_200_OK)
def libro_registro(
    year: int = Query(...),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: LibroRegistroService = Depends(get_libro_registro_service),
) -> LibroRegistroOut:
    data = service.compute(company_id, year)
    return LibroRegistroOut(
        year=data["year"],
        emitidas=[RegistroFacturaOut(**r) for r in data["emitidas"]],
        recibidas=[RegistroFacturaOut(**r) for r in data["recibidas"]],
        total_emitidas=data["total_emitidas"],
        total_recibidas=data["total_recibidas"],
    )
