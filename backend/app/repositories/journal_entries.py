from sqlalchemy.orm import Session, joinedload

from ..models import Account, JournalEntry, JournalLine
from .base import BaseRepository


class JournalEntryRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, JournalEntry)

    def get_with_lines(self, entry_id: int, company_id=None):
        q = (
            self.db.query(JournalEntry)
            .options(
                joinedload(JournalEntry.lines),
                joinedload(JournalEntry.author_user),
            )
            .filter(JournalEntry.id == entry_id)
        )
        if company_id is not None:
            q = q.filter(JournalEntry.company_id == company_id)
        return q.first()

    def list_entries(
        self,
        company_id,
        date_from=None,
        date_to=None,
        limit: int = 50,
        offset: int = 0,
    ):
        q = (
            self.db.query(JournalEntry)
            .options(
                joinedload(JournalEntry.lines),
                joinedload(JournalEntry.author_user),
            )
            .filter(JournalEntry.company_id == company_id)
        )
        if date_from is not None:
            q = q.filter(JournalEntry.date >= date_from)
        if date_to is not None:
            q = q.filter(JournalEntry.date <= date_to)
        return q.order_by(JournalEntry.id).offset(offset).limit(limit).all()

    def create_entry_with_lines(self, entry_data: dict, lines_data: list[dict]) -> JournalEntry:
        entry = JournalEntry(**entry_data)
        self.db.add(entry)
        self.db.flush()
        for line_data in lines_data:
            self.db.add(JournalLine(entry_id=entry.id, **line_data))
        return entry

    def replace_lines(self, entry: JournalEntry, lines_data: list[dict]):
        for line in list(entry.lines):
            self.db.delete(line)
        self.db.flush()
        for line_data in lines_data:
            self.db.add(JournalLine(entry_id=entry.id, **line_data))

    def get_account(self, account_id: int, company_id=None) -> Account | None:
        q = self.db.query(Account).filter(Account.id == account_id)
        if company_id is not None:
            q = q.filter(Account.company_id == company_id)
        return q.first()
