from datetime import date as DateType

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import AuditLog, JournalEntry, User
from ..repositories.journal_entries import JournalEntryRepository
from ..schemas.journal_entries import JournalEntryIn, JournalEntryOut
from ..services.journal_entries import JournalEntryService

router = APIRouter(tags=["journal-entries"])


def get_journal_entry_service(
    db: Session = Depends(get_db),
) -> JournalEntryService:
    return JournalEntryService(JournalEntryRepository(db))


def _http_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    if detail == "Asiento no existe":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post("/journal-entries", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/entries", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/asientos", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    body: JournalEntryIn,
    user: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
    db: Session = Depends(get_db),
) -> JournalEntry:
    try:
        entry = service.create_entry(body, company_id, user.id)
    except ValueError as exc:
        raise _http_error(exc)
    db.add(
        AuditLog(
            company_id=company_id,
            user_id=user.id,
            user_email=user.email,
            action="journal_entry.create",
            target_type="journal_entry",
            target_id=entry.id,
            detail={"description": body.description, "date": str(body.date)},
        )
    )
    db.commit()
    return entry


@router.get("/journal-entries", response_model=list[JournalEntryOut])
@router.get("/entries", response_model=list[JournalEntryOut])
@router.get("/asientos", response_model=list[JournalEntryOut])
def list_entries(
    date_from: DateType | None = Query(default=None),
    start_date: DateType | None = Query(default=None),
    from_date: DateType | None = Query(default=None),
    date_to: DateType | None = Query(default=None),
    end_date: DateType | None = Query(default=None),
    to_date: DateType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> list[JournalEntry]:
    start = date_from or start_date or from_date
    end = date_to or end_date or to_date
    return service.list_entries(company_id, start, end, limit, offset)


@router.put("/journal-entries/{entry_id}", response_model=JournalEntryOut)
@router.put("/entries/{entry_id}", response_model=JournalEntryOut)
@router.put("/asientos/{entry_id}", response_model=JournalEntryOut)
def update_entry(
    entry_id: int,
    body: JournalEntryIn,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> JournalEntry:
    try:
        return service.update_entry(entry_id, body, company_id)
    except ValueError as exc:
        raise _http_error(exc)


@router.post("/journal-entries/{entry_id}/annul", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/annul", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/annul", response_model=JournalEntryOut)
@router.post("/journal-entries/{entry_id}/anular", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/anular", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/anular", response_model=JournalEntryOut)
def annul_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> JournalEntry:
    try:
        return service.annul_entry(entry_id, company_id)
    except ValueError as exc:
        raise _http_error(exc)


@router.post("/journal-entries/{entry_id}/review", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/review", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/review", response_model=JournalEntryOut)
@router.post("/journal-entries/{entry_id}/revisar", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/revisar", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/revisar", response_model=JournalEntryOut)
def review_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> JournalEntry:
    try:
        return service.review_entry(entry_id, company_id)
    except ValueError as exc:
        raise _http_error(exc)


@router.post("/journal-entries/{entry_id}/accept", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/accept", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/accept", response_model=JournalEntryOut)
@router.post("/journal-entries/{entry_id}/aceptar", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/aceptar", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/aceptar", response_model=JournalEntryOut)
def accept_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> JournalEntry:
    try:
        return service.accept_entry(entry_id, company_id)
    except ValueError as exc:
        raise _http_error(exc)


@router.post("/journal-entries/{entry_id}/correct", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/entries/{entry_id}/correct", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/asientos/{entry_id}/correct", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/journal-entries/{entry_id}/corregir", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/entries/{entry_id}/corregir", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/asientos/{entry_id}/corregir", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
def correct_entry(
    entry_id: int,
    body: JournalEntryIn,
    user: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> JournalEntry:
    try:
        return service.correct_entry(entry_id, body, user.id, company_id)
    except ValueError as exc:
        raise _http_error(exc)


@router.delete("/journal-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/asientos/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/journal-entries/{entry_id}/eliminar", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/entries/{entry_id}/eliminar", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/asientos/{entry_id}/eliminar", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/journal-entries/{entry_id}/borrar", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/entries/{entry_id}/borrar", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/asientos/{entry_id}/borrar", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    company_id: int | None = Depends(active_company_id_dep),
    service: JournalEntryService = Depends(get_journal_entry_service),
) -> None:
    try:
        service.delete_entry(entry_id, company_id)
    except ValueError as exc:
        raise _http_error(exc)
    return None
