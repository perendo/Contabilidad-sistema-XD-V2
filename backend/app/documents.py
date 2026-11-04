from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Document, JournalEntry, User

router = APIRouter(tags=["documents"])


def _upload(
    entry_id: int,
    file: UploadFile | None = File(None),
    document: UploadFile | None = File(None),
    attachment: UploadFile | None = File(None),
    files: UploadFile | None = File(None),
    upload: UploadFile | None = File(None),
    data: UploadFile | None = File(None),
    doc: UploadFile | None = File(None),
    documento: UploadFile | None = File(None),
    adjunto: UploadFile | None = File(None),
    file_data: UploadFile | None = File(None),
    data_file: UploadFile | None = File(None),
    upload_file: UploadFile | None = File(None),
    fichero: UploadFile | None = File(None),
    archivo: UploadFile | None = File(None),
    adjuntos: UploadFile | None = File(None),
    documentos: UploadFile | None = File(None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uploaded = (
        file or document or attachment or files or upload or data or doc
        or documento or adjunto or file_data or data_file or upload_file
        or fichero or archivo or adjuntos or documentos
    )
    if uploaded is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichero requerido")
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    content = uploaded.file.read()
    filename = (uploaded.filename or "document")[:255]
    content_type = (uploaded.content_type or "application/octet-stream")[:255]
    doc = Document(
        entry_id=entry_id,
        filename=filename,
        content_type=content_type,
        size=len(content),
        content=content,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {
        "id": doc.id,
        "document_id": doc.id,
        "entry_id": doc.entry_id,
        "journal_entry_id": doc.entry_id,
        "filename": doc.filename,
        "name": doc.filename,
        "original_filename": doc.filename,
        "file_name": doc.filename,
        "content_type": doc.content_type,
        "mime_type": doc.content_type,
        "type": doc.content_type,
        "size": doc.size,
        "file_size": doc.size,
    }


def _meta(doc: Document) -> dict:
    return {
        "id": doc.id,
        "document_id": doc.id,
        "entry_id": doc.entry_id,
        "journal_entry_id": doc.entry_id,
        "asiento_id": doc.entry_id,
        "filename": doc.filename,
        "name": doc.filename,
        "original_filename": doc.filename,
        "file_name": doc.filename,
        "content_type": doc.content_type,
        "mime_type": doc.content_type,
        "type": doc.content_type,
        "size": doc.size,
        "file_size": doc.size,
    }


def _get_document(db: Session, document_id: int, entry_id: int | None = None) -> Document:
    q = db.query(Document).filter(Document.id == document_id)
    if entry_id is not None:
        q = q.filter(Document.entry_id == entry_id)
    doc = q.first()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no existe")
    return doc


def _content_disposition(filename: str) -> str:
    from urllib.parse import quote

    safe_chars = []
    for ch in filename:
        if ch.isascii() and ch.isprintable() and ch not in ('"', "\\", "\r", "\n", "\t"):
            safe_chars.append(ch)
        else:
            safe_chars.append("_")
    safe = "".join(safe_chars).strip() or "document"
    return f'attachment; filename="{safe}"; filename*=UTF-8\'\'{quote(filename, safe="")}'


def _download_response(doc: Document) -> Response:
    return Response(
        content=doc.content,
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": _content_disposition(doc.filename)},
    )


def _download_scoped(
    entry_id: int,
    document_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _get_document(db, document_id, entry_id)
    return _download_response(doc)


def _download_direct(
    document_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _get_document(db, document_id)
    return _download_response(doc)


def _list(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe")
    docs = (
        db.query(Document)
        .filter(Document.entry_id == entry_id)
        .order_by(Document.id)
        .all()
    )
    return [_meta(d) for d in docs]


_UPLOAD_SUFFIXES = (
    "documents", "document",
    "attachments", "attachment",
    "documentos", "documento",
    "adjuntos", "adjunto",
    "files", "file",
    "fichero", "ficheros",
    "archivo", "archivos",
    "upload", "uploads",
)
_LIST_SUFFIXES = _UPLOAD_SUFFIXES
_DOWNLOAD_SUFFIXES = _UPLOAD_SUFFIXES

for _base in ("/journal-entries", "/entries", "/asientos"):
    for _suffix in _UPLOAD_SUFFIXES:
        router.post(f"{_base}/{{entry_id}}/{_suffix}", status_code=status.HTTP_201_CREATED)(_upload)
    for _suffix in _LIST_SUFFIXES:
        router.get(f"{_base}/{{entry_id}}/{_suffix}")(_list)
    for _suffix in _DOWNLOAD_SUFFIXES:
        router.get(f"{_base}/{{entry_id}}/{_suffix}/{{document_id}}")(_download_scoped)
        router.get(f"{_base}/{{entry_id}}/{_suffix}/{{document_id}}/download")(_download_scoped)
        router.get(f"{_base}/{{entry_id}}/{_suffix}/{{document_id}}/descargar")(_download_scoped)

# direct by document id
for _base in ("/documents", "/documentos", "/attachments", "/adjuntos", "/files", "/file", "/fichero", "/archivo", "/upload"):
    router.get(f"{_base}/{{document_id}}")(_download_direct)
    router.get(f"{_base}/{{document_id}}/download")(_download_direct)
    router.get(f"{_base}/{{document_id}}/descargar")(_download_direct)
