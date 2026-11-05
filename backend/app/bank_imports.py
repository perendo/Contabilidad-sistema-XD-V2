import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from openpyxl import load_workbook
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import (
    Account,
    BankIbanAccount,
    JournalEntry,
    JournalLine,
    User,
)

router = APIRouter(tags=["bank-imports"])

SUSPENSE_CODE = "555"
BANK_CODE_PREFIX = "57"

HEADER_ALIASES = {
    "date": {"fecha operacion", "fecha"},
    "concept": {"concepto", "descripcion"},
    "amount": {"importe", "cantidad"},
}

IBAN_RE = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}")
DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")


class BankImportOut(BaseModel):
    iban: str
    created: int
    entry_ids: list[int]


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.strip().lower().split())


def _find_iban(rows: list[list[object]]) -> str:
    for row in rows:
        for value in row:
            if not isinstance(value, str):
                continue
            candidate = re.sub(r"\s+", "", value).upper()
            if IBAN_RE.fullmatch(candidate):
                return candidate
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No se ha encontrado ningún IBAN en el fichero",
    )


def _find_header(rows: list[list[object]]) -> tuple[int, dict[str, int]]:
    for index, row in enumerate(rows):
        columns: dict[str, int] = {}
        for position, value in enumerate(row):
            name = _normalize(value) if value is not None else ""
            for key, aliases in HEADER_ALIASES.items():
                if key not in columns and name in aliases:
                    columns[key] = position
        if len(columns) == len(HEADER_ALIASES):
            return index, columns
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No se han reconocido las cabeceras del fichero",
    )


def _parse_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("fecha inválida")


def _parse_amount(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("importe inválido")
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    text = str(value).strip().replace(" ", "")
    if not text:
        raise ValueError("importe inválido")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("importe inválido") from exc


def _movements(rows: list[list[object]]) -> list[tuple[int, object, object, object]]:
    header_index, columns = _find_header(rows)
    result = []
    for index in range(header_index + 1, len(rows)):
        row = rows[index]
        values = {
            key: row[position] if position < len(row) else None
            for key, position in columns.items()
        }
        if all(value in (None, "") for value in values.values()):
            continue
        result.append(
            (index + 1, values["date"], values["concept"], values["amount"])
        )
    return result


@router.post(
    "/bank-imports",
    response_model=BankImportOut,
    status_code=status.HTTP_201_CREATED,
)
def import_bank_movements(
    file: UploadFile = File(...),
    account_id: int | None = Form(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankImportOut:
    workbook = load_workbook(BytesIO(file.file.read()), data_only=True)
    sheet = workbook.active
    rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    iban = _find_iban(rows)
    movements = _movements(rows)

    parsed: list[tuple[int, date, str, Decimal]] = []
    errors: list[str] = []
    for line_number, raw_date, concept, raw_amount in movements:
        try:
            parsed.append(
                (
                    line_number,
                    _parse_date(raw_date),
                    str(concept) if concept is not None else "",
                    _parse_amount(raw_amount),
                )
            )
        except ValueError as exc:
            errors.append(f"Fila {line_number}: {exc}")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors)
        )

    mapping = (
        db.query(BankIbanAccount).filter(BankIbanAccount.iban == iban).first()
    )

    if account_id is None:
        if mapping is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El IBAN {iban} no está vinculado a ninguna cuenta contable",
            )
        bank = mapping.account
    else:
        bank = db.query(Account).filter(Account.id == account_id).first()
        if bank is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cuenta no existe"
            )

    if not bank.code.startswith(BANK_CODE_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La cuenta {bank.code} no es una cuenta de tesorería (57)",
        )
    if not bank.is_detail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La cuenta {bank.code} no es una subcuenta de detalle",
        )

    suspense = db.query(Account).filter(Account.code == SUSPENSE_CODE).first()
    if suspense is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La cuenta {SUSPENSE_CODE} no existe",
        )

    entries: list[JournalEntry] = []
    try:
        if mapping is None:
            db.add(BankIbanAccount(iban=iban, account_id=bank.id))
        elif mapping.account_id != bank.id:
            mapping.account_id = bank.id

        for _, entry_date, concept, amount in parsed:
            entry = JournalEntry(
                date=entry_date,
                description=concept,
                status="draft",
            )
            db.add(entry)
            db.flush()

            if amount >= 0:
                lines = [
                    (bank, amount, Decimal("0")),
                    (suspense, Decimal("0"), amount),
                ]
            else:
                value = -amount
                lines = [
                    (suspense, value, Decimal("0")),
                    (bank, Decimal("0"), value),
                ]

            for account, debit, credit in lines:
                db.add(
                    JournalLine(
                        entry_id=entry.id,
                        account_id=account.id,
                        description=entry.description,
                        debit=debit,
                        credit=credit,
                    )
                )
            entries.append(entry)
        db.commit()
    except Exception:
        db.rollback()
        raise

    for entry in entries:
        db.refresh(entry)

    return BankImportOut(
        iban=iban,
        created=len(entries),
        entry_ids=[entry.id for entry in entries],
    )
