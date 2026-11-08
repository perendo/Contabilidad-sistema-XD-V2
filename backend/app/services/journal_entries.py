from datetime import date as DateType
from decimal import Decimal

from ..document_storage import delete_document, move_document
from ..models import JournalEntry, JournalLine
from ..repositories.journal_entries import JournalEntryRepository
from ..schemas.journal_entries import (
    ALLOWED_STATUSES,
    JournalEntryIn,
    JournalLineIn,
)


class JournalEntryService:
    def __init__(self, repo: JournalEntryRepository):
        self.repo = repo

    def validate(self, body: JournalEntryIn, company_id=None) -> None:
        if len(body.lines) < 2:
            raise ValueError("Se requieren al menos dos líneas")
        if body.status is not None and body.status not in ALLOWED_STATUSES:
            raise ValueError("Estado no válido")
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for line in body.lines:
            if line.debit < 0 or line.credit < 0:
                raise ValueError("Importes no pueden ser negativos")
            account = self.repo.get_account(line.account_id, company_id)
            if account is None:
                raise ValueError("Cuenta no existe")
            if not account.is_detail:
                raise ValueError(
                    f"La cuenta {account.code} ({account.name}) es una cuenta de grupo/balance. "
                    f"Solo se permiten apuntes en subcuentas de detalle (último nivel)."
                )
            total_debit += line.debit
            total_credit += line.credit
        if total_debit != total_credit:
            raise ValueError("El asiento no cuadra")

    def add_accepted_entry(
        self,
        *,
        entry_date: DateType,
        description: str,
        lines: list[JournalLineIn],
        company_id=None,
        author_id=None,
    ) -> JournalEntry:
        """Valida y añade un asiento aceptado a la sesión, sin confirmar la transacción."""
        body = JournalEntryIn(
            date=entry_date,
            description=description,
            lines=lines,
        )
        self.validate(body, company_id)
        entry = JournalEntry(
            date=entry_date,
            description=description,
            status="accepted",
            company_id=company_id,
            author_id=author_id,
        )
        self.repo.db.add(entry)
        self.repo.db.flush()
        for line in lines:
            self.repo.db.add(
                JournalLine(
                    entry_id=entry.id,
                    account_id=line.account_id,
                    description=line.description,
                    debit=line.debit,
                    credit=line.credit,
                )
            )
        return entry

    def list_entries(
        self,
        company_id,
        date_from=None,
        date_to=None,
        limit: int = 50,
        offset: int = 0,
    ):
        return self.repo.list_entries(company_id, date_from, date_to, limit, offset)

    def create_entry(self, body: JournalEntryIn, company_id, author_id) -> JournalEntry:
        self.validate(body, company_id)
        entry_status = body.status if body.status is not None else "accepted"
        entry_data = {
            "date": body.date,
            "description": body.description,
            "status": entry_status,
            "company_id": company_id,
            "author_id": author_id,
        }
        lines_data = [
            {
                "account_id": line.account_id,
                "description": line.description,
                "debit": line.debit,
                "credit": line.credit,
            }
            for line in body.lines
        ]
        entry = self.repo.create_entry_with_lines(entry_data, lines_data)
        self.repo.db.commit()
        self.repo.db.refresh(entry)
        return entry

    def update_entry(
        self,
        entry_id: int,
        body: JournalEntryIn,
        company_id=None,
    ) -> JournalEntry:
        entry = self.repo.get_with_lines(entry_id, company_id)
        if entry is None:
            raise ValueError("Asiento no existe")
        if entry.status != "draft":
            raise ValueError("Solo se pueden editar asientos en borrador")
        body.status = None
        self.validate(body, company_id)
        previous_year = entry.date.year
        entry.date = body.date
        entry.description = body.description
        if entry.date.year != previous_year:
            for doc in entry.documents:
                doc.file_path = move_document(doc, entry, self.repo.db)
        self.repo.replace_lines(
            entry,
            [
                {
                    "account_id": line.account_id,
                    "description": line.description,
                    "debit": line.debit,
                    "credit": line.credit,
                }
                for line in body.lines
            ],
        )
        self.repo.db.commit()
        self.repo.db.refresh(entry)
        return entry

    def annul_entry(self, entry_id: int, company_id=None) -> JournalEntry:
        entry = self.repo.get_with_lines(entry_id, company_id)
        if entry is None:
            raise ValueError("Asiento no existe")
        if entry.status != "draft":
            raise ValueError("Solo se pueden anular asientos en borrador")
        entry.status = "annulled"
        self.repo.db.commit()
        self.repo.db.refresh(entry)
        return entry

    def review_entry(self, entry_id: int, company_id=None) -> JournalEntry:
        entry = self.repo.get_with_lines(entry_id, company_id)
        if entry is None:
            raise ValueError("Asiento no existe")
        if entry.status != "draft":
            raise ValueError("Solo se pueden revisar asientos en borrador")
        entry.reviewed = True
        self.repo.db.commit()
        self.repo.db.refresh(entry)
        return entry

    def accept_entry(self, entry_id: int, company_id=None) -> JournalEntry:
        entry = self.repo.get_with_lines(entry_id, company_id)
        if entry is None:
            raise ValueError("Asiento no existe")
        if entry.status != "draft":
            raise ValueError("Solo se pueden aceptar asientos en borrador")
        if not entry.reviewed:
            raise ValueError(
                "El asiento debe estar revisado antes de aceptarse"
            )
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for line in entry.lines:
            account = self.repo.get_account(line.account_id, company_id)
            if account is None or not account.is_detail:
                raise ValueError("Cuenta no válida para el asiento")
            total_debit += line.debit
            total_credit += line.credit
        if total_debit != total_credit:
            raise ValueError("El asiento no cuadra")
        entry.status = "accepted"
        self.repo.db.commit()
        self.repo.db.refresh(entry)
        return entry

    def correct_entry(
        self,
        entry_id: int,
        body: JournalEntryIn,
        author_id: int,
        company_id=None,
    ) -> JournalEntry:
        original = self.repo.get_with_lines(entry_id, company_id)
        if original is None:
            raise ValueError("Asiento no existe")
        if original.status != "accepted":
            raise ValueError("Solo se pueden corregir asientos aceptados")
        self.validate(body, company_id)
        entry = JournalEntry(
            date=body.date,
            description=body.description,
            status="accepted",
            correction_of_entry_id=original.id,
            company_id=company_id if company_id is not None else original.company_id,
            author_id=author_id,
        )
        self.repo.db.add(entry)
        self.repo.db.flush()
        for line in body.lines:
            self.repo.db.add(
                JournalLine(
                    entry_id=entry.id,
                    account_id=line.account_id,
                    description=line.description,
                    debit=line.debit,
                    credit=line.credit,
                )
            )
        self.repo.db.commit()
        self.repo.db.refresh(entry)
        return entry

    def delete_entry(self, entry_id: int, company_id=None) -> None:
        entry = self.repo.get_with_lines(entry_id, company_id)
        if entry is None:
            raise ValueError("Asiento no existe")
        if entry.status != "draft":
            raise ValueError("Solo se pueden borrar asientos en borrador")
        file_paths = [doc.file_path for doc in entry.documents]
        self.repo.db.delete(entry)
        self.repo.db.commit()
        for file_path in file_paths:
            try:
                delete_document(file_path)
            except (OSError, ValueError):
                pass
