from datetime import date
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[str] = mapped_column(String(50))
    address: Mapped[str] = mapped_column(String(500))
    fiscal_year: Mapped[str] = mapped_column(String(20))


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column()
    is_detail: Mapped[bool] = mapped_column(default=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    parent: Mapped["Account | None"] = relationship("Account", remote_side=[id], back_populates="children")
    children: Mapped[list["Account"]] = relationship("Account", back_populates="parent")


class BankIbanAccount(Base):
    __tablename__ = "bank_iban_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    iban: Mapped[str] = mapped_column(String(34), unique=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped["Account"] = relationship("Account")


class BankImportProfile(Base):
    __tablename__ = "bank_import_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    iban: Mapped[str] = mapped_column(String(34), unique=True, index=True)
    date_column: Mapped[str] = mapped_column(String(255))
    concept_column: Mapped[str] = mapped_column(String(255))
    amount_column: Mapped[str] = mapped_column(String(255))


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default="accepted")
    reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)
    correction_of_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("journal_entries.id"), nullable=True
    )

    @property
    def corrects_entry_id(self) -> int | None:
        return self.correction_of_entry_id

    @property
    def original_entry_id(self) -> int | None:
        return self.correction_of_entry_id
    lines: Mapped[list["JournalLine"]] = relationship(
        "JournalLine", back_populates="entry", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="entry", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    size: Mapped[int] = mapped_column(default=0)
    file_path: Mapped[str] = mapped_column(String(500))

    entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="documents")


class ThirdParty(Base):
    __tablename__ = "third_parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(50))
    address: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(255), default="")

    account: Mapped["Account"] = relationship("Account")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("year", "number", name="uq_invoices_year_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column()
    number: Mapped[int] = mapped_column()
    date: Mapped[date] = mapped_column(Date)
    third_party_id: Mapped[int] = mapped_column(ForeignKey("third_parties.id"))
    description: Mapped[str] = mapped_column(String(500), default="")
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    irpf_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    irpf_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pendiente")

    third_party: Mapped["ThirdParty"] = relationship("ThirdParty")
    entry: Mapped["JournalEntry | None"] = relationship("JournalEntry")


class ReceivedInvoice(Base):
    __tablename__ = "received_invoices"
    __table_args__ = (
        UniqueConstraint(
            "third_party_id", "supplier_number", name="uq_received_invoices_supplier_number"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    third_party_id: Mapped[int] = mapped_column(ForeignKey("third_parties.id"))
    supplier_number: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    irpf_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    irpf_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    expense_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pendiente")

    third_party: Mapped["ThirdParty"] = relationship("ThirdParty")
    expense_account: Mapped["Account"] = relationship("Account")
    entry: Mapped["JournalEntry | None"] = relationship("JournalEntry")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    description: Mapped[str] = mapped_column(String(500), default="")
    debit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account")
