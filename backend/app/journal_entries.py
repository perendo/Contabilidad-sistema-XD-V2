from datetime import date as DateType
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from sqlalchemy.orm import Session, joinedload

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .document_storage import delete_document, move_document
from .models import Account, JournalEntry, JournalLine, User

router = APIRouter(tags=["journal-entries"])


class JournalLineIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    account_id: int = Field(validation_alias=AliasChoices("account_id", "accountId", "cuenta_id"))
    description: str = Field(default="", validation_alias=AliasChoices("description", "concept", "concepto"))
    debit: Decimal = Field(default=Decimal("0"), validation_alias=AliasChoices("debit", "debe"))
    credit: Decimal = Field(default=Decimal("0"), validation_alias=AliasChoices("credit", "haber"))


class JournalEntryIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: DateType = Field(validation_alias=AliasChoices("date", "fecha"))
    description: str = Field(default="", validation_alias=AliasChoices("description", "concept", "concepto"))
    status: str | None = Field(default=None, validation_alias=AliasChoices("status", "estado"))
    lines: list[JournalLineIn] = Field(validation_alias=AliasChoices("lines", "lineas", "apuntes"))


class JournalLineOut(BaseModel):
    id: int
    account_id: int
    description: str
    debit: Decimal
    credit: Decimal
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: lambda v: f"{v:.2f}"})


class JournalEntryOut(BaseModel):
    id: int
    date: DateType
    description: str
    status: str
    reviewed: bool
    author: str | None = None
    correction_of_entry_id: int | None = None
    corrects_entry_id: int | None = None
    original_entry_id: int | None = None
    lines: list[JournalLineOut]
    model_config = ConfigDict(from_attributes=True)


ALLOWED_STATUSES = {"draft", "accepted"}


def _validate(body: JournalEntryIn, db: Session, company_id: int | None = None) -> None:
    if len(body.lines) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se requieren al menos dos líneas")
    if body.status is not None and body.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado no válido")
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line in body.lines:
        if line.debit < 0 or line.credit < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Importes no pueden ser negativos")
        q = db.query(Account).filter(Account.id == line.account_id)
        if company_id is not None:
            q = q.filter(Account.company_id == company_id)
        account = q.first()
        if account is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuenta no existe")
        if not account.is_detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La cuenta {account.code} ({account.name}) es una cuenta de grupo/balance. "
                f"Solo se permiten apuntes en subcuentas de detalle (último nivel).",
            )
        total_debit += line.debit
        total_credit += line.credit
    if total_debit != total_credit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El asiento no cuadra")


def add_accepted_entry(
    db: Session,
    *,
    entry_date: DateType,
    description: str,
    lines: list[JournalLineIn],
    company_id: int | None = None,
    author_id: int | None = None,
) -> JournalEntry:
    """Valida y añade un asiento aceptado a la sesión, sin confirmar la transacción."""
    _validate(
        JournalEntryIn(date=entry_date, description=description, lines=lines), db, company_id
    )
    entry = JournalEntry(
        date=entry_date,
        description=description,
        status="accepted",
        company_id=company_id,
        author_id=author_id,
    )
    db.add(entry)
    db.flush()
    for line in lines:
        db.add(
            JournalLine(
                entry_id=entry.id,
                account_id=line.account_id,
                description=line.description,
                debit=line.debit,
                credit=line.credit,
            )
        )
    return entry


@router.post("/journal-entries", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/entries", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
@router.post("/asientos", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    body: JournalEntryIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> JournalEntry:
    _validate(body, db, company_id)
    entry_status = body.status if body.status is not None else "accepted"
    entry = JournalEntry(
        date=body.date,
        description=body.description,
        status=entry_status,
        company_id=company_id,
        author_id=user.id,
    )
    db.add(entry)
    db.flush()
    for line in body.lines:
        db.add(
            JournalLine(
                entry_id=entry.id,
                account_id=line.account_id,
                description=line.description,
                debit=line.debit,
                credit=line.credit,
            )
        )
    db.commit()
    db.refresh(entry)
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> list[JournalEntry]:
    q = (
        db.query(JournalEntry)
        .options(
            joinedload(JournalEntry.lines),
            joinedload(JournalEntry.author_user),
        )
        .filter(JournalEntry.company_id == company_id)
    )
    start = date_from or start_date or from_date
    end = date_to or end_date or to_date
    if start is not None:
        q = q.filter(JournalEntry.date >= start)
    if end is not None:
        q = q.filter(JournalEntry.date <= end)
    return q.order_by(JournalEntry.id).all()


@router.put("/journal-entries/{entry_id}", response_model=JournalEntryOut)
@router.put("/entries/{entry_id}", response_model=JournalEntryOut)
@router.put("/asientos/{entry_id}", response_model=JournalEntryOut)
def update_entry(
    entry_id: int,
    body: JournalEntryIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> JournalEntry:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    entry = q.first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    if entry.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden editar asientos en borrador")
    # ignore status changes via update; keep draft
    body.status = None
    _validate(body, db, company_id)
    previous_year = entry.date.year
    entry.date = body.date
    entry.description = body.description
    if entry.date.year != previous_year:
        for doc in entry.documents:
            doc.file_path = move_document(doc, entry, db)
    # replace lines
    for line in list(entry.lines):
        db.delete(line)
    db.flush()
    for line in body.lines:
        db.add(
            JournalLine(
                entry_id=entry.id,
                account_id=line.account_id,
                description=line.description,
                debit=line.debit,
                credit=line.credit,
            )
        )
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/journal-entries/{entry_id}/annul", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/annul", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/annul", response_model=JournalEntryOut)
@router.post("/journal-entries/{entry_id}/anular", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/anular", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/anular", response_model=JournalEntryOut)
def annul_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> JournalEntry:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    entry = q.first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    if entry.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden anular asientos en borrador")
    entry.status = "annulled"
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/journal-entries/{entry_id}/review", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/review", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/review", response_model=JournalEntryOut)
@router.post("/journal-entries/{entry_id}/revisar", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/revisar", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/revisar", response_model=JournalEntryOut)
def review_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> JournalEntry:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    entry = q.first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    if entry.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden revisar asientos en borrador",
        )
    entry.reviewed = True
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/journal-entries/{entry_id}/accept", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/accept", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/accept", response_model=JournalEntryOut)
@router.post("/journal-entries/{entry_id}/aceptar", response_model=JournalEntryOut)
@router.post("/entries/{entry_id}/aceptar", response_model=JournalEntryOut)
@router.post("/asientos/{entry_id}/aceptar", response_model=JournalEntryOut)
def accept_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> JournalEntry:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    entry = q.first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    if entry.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden aceptar asientos en borrador",
        )
    if not entry.reviewed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El asiento debe estar revisado antes de aceptarse",
        )
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line in entry.lines:
        aq = db.query(Account).filter(Account.id == line.account_id)
        if company_id is not None:
            aq = aq.filter(Account.company_id == company_id)
        account = aq.first()
        if account is None or not account.is_detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cuenta no válida para el asiento",
            )
        total_debit += line.debit
        total_credit += line.credit
    if total_debit != total_credit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El asiento no cuadra"
        )
    entry.status = "accepted"
    db.commit()
    db.refresh(entry)
    return entry


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
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> JournalEntry:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    original = q.first()
    if original is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    if original.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden corregir asientos aceptados",
        )
    _validate(body, db, company_id)
    entry = JournalEntry(
        date=body.date,
        description=body.description,
        status="accepted",
        correction_of_entry_id=original.id,
        company_id=company_id if company_id is not None else original.company_id,
        author_id=user.id,
    )
    db.add(entry)
    db.flush()
    for line in body.lines:
        db.add(
            JournalLine(
                entry_id=entry.id,
                account_id=line.account_id,
                description=line.description,
                debit=line.debit,
                credit=line.credit,
            )
        )
    db.commit()
    db.refresh(entry)
    return entry

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
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> None:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    entry = q.first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    if entry.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden borrar asientos en borrador",
        )
    file_paths = [doc.file_path for doc in entry.documents]
    db.delete(entry)
    db.commit()
    for file_path in file_paths:
        try:
            delete_document(file_path)
        except (OSError, ValueError):
            pass
    return None
