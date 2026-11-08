from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_context import active_company_id_dep
from ..database import get_db
from ..models import Document, JournalEntry, User
from ..repositories.documents import DocumentRepository
from ..schemas.documents import (
    ALLOWED_MIME_TYPES,
    AttachmentOut,
    MAX_FILE_SIZE,
)
from ..services.documents import DocumentService

router = APIRouter(tags=["documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(DocumentRepository(db))


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
    company_id: int | None = Depends(active_company_id_dep),
    service: DocumentService = Depends(get_document_service),
) -> AttachmentOut:
    q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
    if company_id is not None:
        q = q.filter(JournalEntry.company_id == company_id)
    entry = q.first()
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

    try:
        doc = service.upload_attachment(
            entry,
            file.filename or "document",
            content_type,
            content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return doc


@router.get(
    "/journal-entries/{entry_id}/attachments",
    response_model=list[AttachmentOut],
)
def list_attachments(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
    service: DocumentService = Depends(get_document_service),
) -> list[Document]:
    docs = service.list_documents(entry_id, company_id)
    if docs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no existe"
        )
    return docs


@router.get("/attachments/{attachment_id}")
def download_attachment(
    attachment_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
    service: DocumentService = Depends(get_document_service),
) -> Response:
    doc = service.get_document(attachment_id, company_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no existe"
        )
    try:
        content = service.download_document(doc)
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no existe"
        ) from None
    return Response(
        content=content,
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": service.content_disposition(doc.filename)},
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
    service: DocumentService = Depends(get_document_service),
) -> None:
    doc = service.get_document(attachment_id, company_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no existe"
        )
    service.delete_document(doc)
    return None
