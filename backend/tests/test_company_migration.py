import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Company

engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _session() -> Session:
    return TestingSessionLocal()


def test_creates_default_company_when_none_exists():
    db = _session()
    try:
        db.query(Company).delete()
        db.commit()

        from app.company_migration import migrate_existing_to_default_company

        company_id = migrate_existing_to_default_company(db)

        assert company_id is not None
        company = db.query(Company).filter(Company.id == company_id).first()
        assert company is not None
        assert db.query(Company).count() == 1
    finally:
        db.close()


def test_backfills_null_company_id_across_data_tables():
    db = _session()
    try:
        from datetime import date
        from decimal import Decimal

        from app.company_migration import migrate_existing_to_default_company
        from app.models import (
            Account,
            BankIbanAccount,
            BankImportProfile,
            Invoice,
            JournalEntry,
            ReceivedInvoice,
            ThirdParty,
        )

        # filas con company_id NULL
        account = Account(code="100", name="Cuenta", type="Activo", level=1, is_detail=True, company_id=None)
        db.add(account)
        db.flush()

        entry = JournalEntry(date=date(2026, 1, 1), description="Asiento", status="accepted", company_id=None)
        db.add(entry)

        third_party = ThirdParty(
            account_id=account.id,
            name="Tercero",
            tax_id="B123",
            type="Cliente",
            company_id=None,
        )
        db.add(third_party)
        db.flush()

        invoice = Invoice(
            year=2026,
            number=1,
            date=date(2026, 1, 2),
            third_party_id=third_party.id,
            base_amount=Decimal("100.00"),
            vat_rate=Decimal("21.00"),
            vat_amount=Decimal("21.00"),
            total=Decimal("121.00"),
            company_id=None,
        )
        db.add(invoice)

        received = ReceivedInvoice(
            date=date(2026, 1, 3),
            third_party_id=third_party.id,
            supplier_number="F-1",
            base_amount=Decimal("50.00"),
            vat_rate=Decimal("21.00"),
            vat_amount=Decimal("10.50"),
            total=Decimal("60.50"),
            expense_account_id=account.id,
            company_id=None,
        )
        db.add(received)

        iban = BankIbanAccount(iban="ES00", account_id=account.id, company_id=None)
        db.add(iban)

        profile = BankImportProfile(
            iban="ES00",
            date_column="Fecha",
            concept_column="Concepto",
            amount_column="Importe",
            company_id=None,
        )
        db.add(profile)
        db.commit()

        default_id = migrate_existing_to_default_company(db)

        assert account.id is not None
        refreshed_account = db.query(Account).filter(Account.id == account.id).first()
        assert refreshed_account.company_id == default_id

        assert db.query(JournalEntry).filter(JournalEntry.id == entry.id).first().company_id == default_id
        assert db.query(ThirdParty).filter(ThirdParty.id == third_party.id).first().company_id == default_id
        assert db.query(Invoice).filter(Invoice.id == invoice.id).first().company_id == default_id
        assert db.query(ReceivedInvoice).filter(ReceivedInvoice.id == received.id).first().company_id == default_id
        assert db.query(BankIbanAccount).filter(BankIbanAccount.id == iban.id).first().company_id == default_id
        assert db.query(BankImportProfile).filter(BankImportProfile.id == profile.id).first().company_id == default_id
    finally:
        db.close()


def test_preserves_already_assigned_company_id():
    db = _session()
    try:
        from app.company_migration import migrate_existing_to_default_company
        from app.models import Account, Company

        other = Company(name="Otra", tax_id="B999", address="", fiscal_year="2026")
        db.add(other)
        db.commit()
        db.refresh(other)

        account = Account(code="200", name="Cuenta2", type="Activo", level=1, is_detail=True, company_id=other.id)
        db.add(account)
        db.commit()

        migrate_existing_to_default_company(db)

        refreshed = db.query(Account).filter(Account.id == account.id).first()
        assert refreshed.company_id == other.id
    finally:
        db.close()


def test_migration_is_idempotent():
    db = _session()
    try:
        from app.company_migration import migrate_existing_to_default_company

        first = migrate_existing_to_default_company(db)
        second = migrate_existing_to_default_company(db)
        assert first == second
        from app.models import Company

        assert db.query(Company).count() == 1
    finally:
        db.close()
