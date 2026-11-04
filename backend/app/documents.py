from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Document, JournalEntry, User

router = APIRouter(tags=["documents"])


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/xml",
    "text/xml",
}


class AttachmentOut(BaseModel):
    id: int
    entry_id: int
    filename: str
    content_type: str
    size: int

    model_config = ConfigDict(from_attributes=True)


def _get_document(db: Session, attachment_id: int) -> Document:
    doc = db.query(Document).filter(Document.id == attachment_id).first()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no existe"
        )
    return doc


def _content_disposition(filename: str) -> str:
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


@router.post(
    "/journal-entries/{entry_id}/attachments",
    response_model=AttachmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    entry_id: int,
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttachmentOut:
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe"
        )

    content_type = (file.content_type or "application/octet-stream")[:255]
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no permitido (solo PDF, PNG, JPG, XML)",
        )

    size = 0
    chunks = []
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="El archivo excede el tamaño máximo permitido (10MB)",
            )
        chunks.append(chunk)

    content = b"".join(chunks)
    doc = Document(
        entry_id=entry_id,
        filename=(file.filename or "document")[:255],
        content_type=content_type,
        size=len(content),
        content=content,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get(
    "/journal-entries/{entry_id}/attachments",
    response_model=list[AttachmentOut],
)
def list_attachments(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Document]:
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe"
        )
    return (
        db.query(Document)
        .filter(Document.entry_id == entry_id)
        .order_by(Document.id)
        .all()
    )


@router.get("/attachments/{attachment_id}")
def download_attachment(
    attachment_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    return _download_response(_get_document(db, attachment_id))


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    doc = _get_document(db, attachment_id)
    db.delete(doc)
    db.commit()
