from sqlalchemy.orm import Session

from ..models import Document, JournalEntry


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document(self, attachment_id: int, company_id=None) -> Document | None:
        doc = self.db.query(Document).filter(Document.id == attachment_id).first()
        if doc is None:
            return None
        if company_id is not None:
            entry = self.db.query(JournalEntry).filter(JournalEntry.id == doc.entry_id).first()
            if entry is None or entry.company_id != company_id:
                return None
        return doc

    def list_documents(self, entry_id: int, company_id=None):
        q = self.db.query(JournalEntry).filter(JournalEntry.id == entry_id)
        if company_id is not None:
            q = q.filter(JournalEntry.company_id == company_id)
        entry = q.first()
        if entry is None:
            return None
        return (
            self.db.query(Document)
            .filter(Document.entry_id == entry_id)
            .order_by(Document.id)
            .all()
        )

    def add(self, doc: Document) -> Document:
        self.db.add(doc)
        self.db.flush()
        return doc

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance) -> None:
        self.db.refresh(instance)

    def delete(self, doc: Document) -> None:
        self.db.delete(doc)
