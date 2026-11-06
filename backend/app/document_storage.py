import re
import shutil
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from .config import settings
from .models import Company, Document, JournalEntry

_MAX_COMPANY_FOLDER_LENGTH = 100
_INVALID_FOLDER_CHARS = re.compile(r"[^A-Za-z0-9\u00c0-\u024f ._-]+")
_VALID_EXTENSION = re.compile(r"\.[a-z0-9]{1,10}")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "application/xml": ".xml",
    "text/xml": ".xml",
}


def documents_root() -> Path:
    return Path(settings.documents_dir).expanduser()


def company_folder_name(name: str | None) -> str:
    cleaned = _INVALID_FOLDER_CHARS.sub("_", (name or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        cleaned = "Empresa"
    if cleaned.upper() in _WINDOWS_RESERVED_NAMES:
        cleaned = f"_{cleaned}"
    return cleaned[:_MAX_COMPANY_FOLDER_LENGTH]


def _company_name(db: Session, entry: JournalEntry | None = None) -> str | None:
    company = None
    if entry is not None and getattr(entry, "company_id", None) is not None:
        company = db.query(Company).filter(Company.id == entry.company_id).first()
    if company is None:
        company = db.query(Company).first()
    return company.name if company is not None else None


def _extension(filename: str, content_type: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if _VALID_EXTENSION.fullmatch(suffix):
        return suffix
    return _CONTENT_TYPE_EXTENSIONS.get(content_type, "")


def _relative_folder(db: Session, entry: JournalEntry) -> Path:
    return Path(company_folder_name(_company_name(db, entry))) / str(entry.date.year)


def build_file_path(
    db: Session, entry: JournalEntry, filename: str, content_type: str
) -> str:
    relative = _relative_folder(db, entry) / generated_filename(filename, content_type)
    return relative.as_posix()


def generated_filename(filename: str, content_type: str) -> str:
    return f"{uuid4().hex}{_extension(filename, content_type)}"


def resolve_path(file_path: str) -> Path:
    root = documents_root().resolve()
    candidate = (root / file_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Ruta de documento fuera del directorio de datos")
    return candidate


def write_document(file_path: str, content: bytes) -> None:
    path = resolve_path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def read_document(file_path: str) -> bytes:
    return resolve_path(file_path).read_bytes()


def delete_document(file_path: str) -> None:
    resolve_path(file_path).unlink(missing_ok=True)


def move_document(doc: Document, entry: JournalEntry, db: Session) -> str:
    old_path = resolve_path(doc.file_path)
    if not old_path.exists():
        return doc.file_path

    relative = _relative_folder(db, entry) / old_path.name
    new_path = resolve_path(relative.as_posix())
    if new_path == old_path:
        return doc.file_path

    new_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old_path), str(new_path))
    return relative.as_posix()
