from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import User
from ..repositories.modelo_347 import Modelo347Repository
from ..schemas.modelo_347 import Modelo347Out, ThirdPartySummaryOut
from ..services.modelo_347 import Modelo347Service

router = APIRouter(tags=["modelo-347"])


def get_modelo_347_service(
    db: Session = Depends(get_db),
) -> Modelo347Service:
    return Modelo347Service(Modelo347Repository(db))


@router.get(
    "/modelo-347",
    response_model=Modelo347Out,
    status_code=status.HTTP_200_OK,
)
def modelo_347(
    year: int = Query(...),
    threshold: float = Query(ge=0),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: Modelo347Service = Depends(get_modelo_347_service),
) -> Modelo347Out:
    data = service.compute(year, threshold, company_id)
    return Modelo347Out(
        year=data["year"],
        threshold=data["threshold"],
        third_parties=[
            ThirdPartySummaryOut(**item) for item in data["third_parties"]
        ],
    )
