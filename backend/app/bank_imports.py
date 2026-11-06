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
    BankImportProfile,
    JournalEntry,
    JournalLine,
    User,
)

router = APIRouter(tags=["bank-imports"])

SUSPENSE_CODE = "555"
BANK_CODE_PREFIX = "57"
MAX_FILE_SIZE = 10 * 1024 * 1024

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


class BankImportProfileIn(BaseModel):
    iban: str
    date_column: str
    concept_column: str
    amount_column: str


class BankImportProfileOut(BaseModel):
    iban: str
    date_column: str
    concept_column: str
    amount_column: str


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
        result = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("importe inválido") from exc
    if result == 0:
        raise ValueError("importe inválido")
    return result


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


def _find_header_by_columns(
    rows: list[list[object]], date_col: str, concept_col: str, amount_col: str
) -> tuple[int, dict[str, int]]:
    target = {_normalize(date_col), _normalize(concept_col), _normalize(amount_col)}
    for index, row in enumerate(rows):
        normalized = [_normalize(v) if v is not None else "" for v in row]
        if target.issubset(set(normalized)):
            columns = {}
            for position, name in enumerate(normalized):
                if name == _normalize(date_col) and "date" not in columns:
                    columns["date"] = position
                if name == _normalize(concept_col) and "concept" not in columns:
                    columns["concept"] = position
                if name == _normalize(amount_col) and "amount" not in columns:
                    columns["amount"] = position
            if len(columns) == 3:
                return index, columns
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No se han reconocido las columnas del perfil en el fichero",
    )


def _movements_with_profile(
    rows: list[list[object]], date_col: str, concept_col: str, amount_col: str
) -> list[tuple[int, object, object, object]]:
    header_index, columns = _find_header_by_columns(rows, date_col, concept_col, amount_col)
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


def _detect_header_row(rows: list[list[object]]) -> list[str]:
    best_index = 0
    best_count = 0
    for index, row in enumerate(rows):
        non_empty = [v for v in row if v not in (None, "")]
        if len(non_empty) > best_count:
            best_count = len(non_empty)
            best_index = index
    if best_count < 2:
        return []
    return [str(v) if v is not None else "" for v in rows[best_index]]


def _save_profile(db: Session, iban: str, date_col: str, concept_col: str, amount_col: str) -> BankImportProfile:
    profile = db.query(BankImportProfile).filter(BankImportProfile.iban == iban).first()
    if profile is None:
        profile = BankImportProfile(
            iban=iban, date_column=date_col, concept_column=concept_col, amount_column=amount_col
        )
        db.add(profile)
    else:
        profile.date_column = date_col
        profile.concept_column = concept_col
        profile.amount_column = amount_col
    db.commit()
    db.refresh(profile)
    return profile


def _parse_norma_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%Y%m%d", "%y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("fecha inválida")


def _parse_norma_importe(text: str) -> Decimal:
    text = text.strip()
    if not text:
        return Decimal("0")
    if not text.isdigit():
        raise ValueError("importe inválido")
    if len(text) <= 4:
        text = text.zfill(5)
    return Decimal(f"{text[:-4] or '0'}.{text[-4:]}")


def _ccc_to_iban(ccc: str) -> str:
    numeric = ccc + "142800"
    remainder = 0
    for char in numeric:
        remainder = (remainder * 10 + int(char)) % 97
    check = 98 - remainder
    if check == 0:
        check = 98
    return f"ES{check:02d}{ccc}"


def _parse_norma_43_file(content: bytes) -> tuple[str, list[tuple[int, date, str, Decimal]]]:
    try:
        text = content.decode("iso-8859-1")
    except (UnicodeDecodeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El fichero no es un Norma 43 válido",
        )

    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El fichero está vacío"
        )

    iban: str | None = None
    for line in lines:
        if line[0:2] == "01":
            field = line[26:60].strip()
            candidate = re.sub(r"\s+", "", field).upper()
            if IBAN_RE.fullmatch(candidate):
                iban = candidate
                break
            if len(candidate) == 20 and candidate.isdigit():
                iban = _ccc_to_iban(candidate)
                break
    if iban is None:
        for line in lines:
            for match in re.finditer(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", line):
                candidate = match.group(0)
                if IBAN_RE.fullmatch(candidate):
                    iban = candidate
                    break
            if iban is not None:
                break
    if iban is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha encontrado ningún IBAN en el fichero",
        )

    parsed: list[tuple[int, date, str, Decimal]] = []
    errors: list[str] = []
    control_count: int | None = None
    control_sum: Decimal | None = None
    for index, line in enumerate(lines, start=1):
        if len(line) != 100:
            errors.append(f"Fila {index}: longitud {len(line)} != 100")
            continue
        code = line[0:2]
        if code == "01":
            continue
        if code in ("21", "22"):
            concept = line[22:70].strip()
            try:
                entry_date = _parse_norma_date(line[6:14])
            except ValueError:
                errors.append(f"Fila {index}: fecha inválida")
                continue
            try:
                importe = _parse_norma_importe(line[70:86])
            except ValueError:
                errors.append(f"Fila {index}: importe inválido")
                continue
            if importe <= 0:
                errors.append(f"Fila {index}: importe inválido")
                continue
            amount = -importe if code == "21" else importe
            parsed.append((index, entry_date, concept, amount))
        elif code == "98":
            raw_count = line[2:8].strip()
            try:
                control_count = int(raw_count) if raw_count else None
            except ValueError:
                control_count = None
            raw_sum = line[8:24].strip()
            try:
                control_sum = _parse_norma_importe(raw_sum) if raw_sum else None
            except ValueError:
                control_sum = None
        else:
            errors.append(f"Fila {index}: código de registro desconocido {code}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors)
        )

    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El fichero no contiene movimientos",
        )

    if control_count is not None and control_count != len(parsed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Control declara {control_count} movimientos, leídos {len(parsed)}",
        )
    if control_sum is not None:
        suma_abs = sum((abs(item[3]) for item in parsed), Decimal("0"))
        if control_sum != suma_abs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Suma control {control_sum} != {suma_abs}",
            )

    return iban, parsed


@router.post(
    "/bank-imports",
    response_model=BankImportOut,
    status_code=status.HTTP_201_CREATED,
)
def import_bank_movements(
    file: UploadFile = File(...),
    account_id: int | None = Form(default=None),
    date_column: str | None = Form(default=None),
    concept_column: str | None = Form(default=None),
    amount_column: str | None = Form(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankImportOut:
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El fichero supera el tamaño máximo de 10 MB",
        )
    filename = (file.filename or "").lower()
    is_excel = filename.endswith(".xlsx") or content.startswith(b"PK")

    if is_excel:
        workbook = load_workbook(BytesIO(content), data_only=True)
        sheet = workbook.active
        rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        iban = _find_iban(rows)
        iban_norm = re.sub(r"\s+", "", iban).upper()

        if date_column and concept_column and amount_column:
            _save_profile(db, iban_norm, date_column, concept_column, amount_column)
            movements = _movements_with_profile(
                rows, date_column, concept_column, amount_column
            )
        else:
            try:
                movements = _movements(rows)
            except HTTPException:
                profile = (
                    db.query(BankImportProfile)
                    .filter(BankImportProfile.iban == iban_norm)
                    .first()
                )
                if profile is not None:
                    movements = _movements_with_profile(
                        rows,
                        profile.date_column,
                        profile.concept_column,
                        profile.amount_column,
                    )
                else:
                    headers = _detect_header_row(rows)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "message": "Se requiere mapeo de columnas",
                            "headers": headers,
                        },
                    )

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
    else:
        iban, parsed = _parse_norma_43_file(content)

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


@router.post(
    "/bank-import-profiles",
    response_model=BankImportProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def save_bank_import_profile(
    payload: BankImportProfileIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankImportProfileOut:
    iban = re.sub(r"\s+", "", payload.iban).upper()
    profile = _save_profile(db, iban, payload.date_column, payload.concept_column, payload.amount_column)
    return BankImportProfileOut(
        iban=profile.iban,
        date_column=profile.date_column,
        concept_column=profile.concept_column,
        amount_column=profile.amount_column,
    )
