from datetime import date as DateType
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import Invoice, User
from ..repositories.accounts import AccountRepository
from ..repositories.invoices import InvoiceRepository
from ..repositories.journal_entries import JournalEntryRepository
from ..repositories.third_parties import ThirdPartyRepository
from ..schemas.invoices import InvoiceIn, InvoiceOut, InvoicePayIn
from ..schemas.journal_entries import JournalEntryIn, JournalEntryOut
from ..services.invoices import InvoiceService
from ..services.journal_entries import JournalEntryService

router = APIRouter(tags=["invoices"])


def get_invoice_service(
    db: Session = Depends(get_db),
) -> InvoiceService:
    return InvoiceService(
        InvoiceRepository(db),
        AccountRepository(db),
        ThirdPartyRepository(db),
        JournalEntryService(JournalEntryRepository(db)),
    )


@router.post(
    "/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED
)
def create_invoice(
    body: InvoiceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
    service: InvoiceService = Depends(get_invoice_service),
) -> Invoice:
    try:
        return service.create_invoice(body, company_id, user.id)
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "número de factura" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
    service: InvoiceService = Depends(get_invoice_service),
) -> list[Invoice]:
    return service.list_invoices(company_id, limit, offset)


@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceOut)
def pay_issued_invoice(
    invoice_id: int,
    body: InvoicePayIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
    service: InvoiceService = Depends(get_invoice_service),
) -> Invoice:
    try:
        return service.pay_issued_invoice(invoice_id, body, company_id, user.id)
    except ValueError as exc:
        detail = str(exc)
        if detail == "Factura no existe":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
