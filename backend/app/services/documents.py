from urllib.parse import quote

from ..document_storage import build_file_path, delete_document, read_document, write_document
from ..models import Document, JournalEntry
from ..repositories.documents import DocumentRepository


class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo

    def get_document(self, attachment_id: int, company_id=None) -> Document | None:
        return self.repo.get_document(attachment_id, company_id)

    def list_documents(self, entry_id: int, company_id=None):
        return self.repo.list_documents(entry_id, company_id)

    def upload_attachment(
        self,
        entry: JournalEntry,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Document:
        file_path = build_file_path(self.repo.db, entry, filename, content_type)
        write_document(file_path, content)
        doc = Document(
            entry_id=entry.id,
            filename=filename[:255],
            content_type=content_type,
            size=len(content),
            file_path=file_path,
        )
        self.repo.add(doc)
        try:
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            delete_document(file_path)
            raise
        self.repo.refresh(doc)
        return doc

    def download_document(self, doc: Document) -> bytes:
        return read_document(doc.file_path)

    def delete_document(self, doc: Document) -> str:
        file_path = doc.file_path
        self.repo.delete(doc)
        self.repo.commit()
        try:
            delete_document(file_path)
        except (OSError, ValueError):
            pass
        return file_path

    @staticmethod
    def content_disposition(filename: str) -> str:
        safe_chars = []
        for ch in filename:
            if ch.isascii() and ch.isprintable() and ch not in ('"', "\\", "\r", "\n", "\t"):
                safe_chars.append(ch)
            else:
                safe_chars.append("_")
        safe = "".join(safe_chars).strip() or "document"
        return f'attachment; filename="{safe}"; filename*=UTF-8\'\'{quote(filename, safe="")}'
