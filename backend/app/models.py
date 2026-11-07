from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
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
    approval_threshold: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_accounts_company_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
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
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    iban: Mapped[str] = mapped_column(String(34), unique=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped["Account"] = relationship("Account")


class BankImportProfile(Base):
    __tablename__ = "bank_import_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    iban: Mapped[str] = mapped_column(String(34), unique=True, index=True)
    date_column: Mapped[str] = mapped_column(String(255))
    concept_column: Mapped[str] = mapped_column(String(255))
    amount_column: Mapped[str] = mapped_column(String(255))


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default="accepted")
    reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)
    correction_of_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("journal_entries.id"), nullable=True
    )

    author_user: Mapped["User | None"] = relationship("User")

    @property
    def author(self) -> str | None:
        return self.author_user.email if self.author_user is not None else None

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
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
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
    __table_args__ = (
        UniqueConstraint(
            "company_id", "year", "number", name="uq_invoices_company_year_number"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
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
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
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
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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


class ReceivedInvoicePending(Base):
    __tablename__ = "received_invoice_pending"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"), nullable=True, index=True
    )
    third_party_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    third_party_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supplier_number: Mapped[str] = mapped_column(String(100))
    date: Mapped[date] = mapped_column(Date)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vat_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    expense_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pendiente")
    reason: Mapped[str] = mapped_column(String(500), default="")
    file_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    company: Mapped["Company | None"] = relationship("Company")


class ReceivedInvoiceJob(Base):
    __tablename__ = "received_invoice_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expense_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="procesando")
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(
        String(255), default="application/octet-stream"
    )
    file_path: Mapped[str] = mapped_column(String(500))
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    company: Mapped["Company | None"] = relationship("Company")
    user: Mapped["User"] = relationship("User")


class CompanyMembership(Base):
    __tablename__ = "company_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_company_memberships_user_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="admin")

    user: Mapped["User"] = relationship("User")
    company: Mapped["Company"] = relationship("Company")
