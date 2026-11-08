from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from ..models import Account, Invoice, ThirdParty
from ..repositories.accounts import AccountRepository
from ..repositories.invoices import InvoiceRepository
from ..repositories.third_parties import ThirdPartyRepository
from ..schemas.invoices import (
    ALLOWED_VAT_RATES,
    CENT,
    InvoiceIn,
    InvoicePayIn,
)
from ..schemas.journal_entries import JournalLineIn
from ..services.journal_entries import JournalEntryService


class InvoiceService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        account_repo: AccountRepository,
        third_party_repo: ThirdPartyRepository,
        journal_service: JournalEntryService,
    ):
        self.invoice_repo = invoice_repo
        self.account_repo = account_repo
        self.third_party_repo = third_party_repo
        self.journal_service = journal_service

    def create_invoice(self, data: InvoiceIn, company_id, author_id) -> Invoice:
        third_party = self.third_party_repo.get(data.third_party_id)
        if third_party is None:
            raise ValueError("Tercero no existe")
        if third_party.type.strip().lower() != "cliente":
            raise ValueError("El tercero no es un cliente")
        if data.base_amount <= 0:
            raise ValueError("La base imponible debe ser positiva")
        if data.vat_rate not in ALLOWED_VAT_RATES:
            raise ValueError("Tipo de IVA no válido")
        sales_account = self.account_repo.get_by_code(company_id, "7000")
        vat_account = self.account_repo.get_by_code(company_id, "4770")
        if sales_account is None or vat_account is None:
            raise ValueError("Cuentas por defecto no encontradas")

        vat_amount = (
            data.base_amount * data.vat_rate / 100
        ).quantize(CENT, rounding=ROUND_HALF_UP)
        irpf_amount = Decimal("0")
        if data.irpf_rate is not None:
            irpf_amount = (
                data.base_amount * data.irpf_rate / 100
            ).quantize(CENT, rounding=ROUND_HALF_UP)
        elif data.irpf_amount is not None:
            irpf_amount = data.irpf_amount
        total = data.base_amount + vat_amount - irpf_amount
        year = data.date.year

        if self.invoice_repo.db.bind.dialect.name == "postgresql":
            self.invoice_repo.db.execute(
                text("SELECT pg_advisory_xact_lock(:year, :company_id)"),
                {"year": year, "company_id": company_id},
            )
        last_number = self.invoice_repo.max_number(year, company_id)
        number = (last_number or 0) + 1
        description = f"Factura {year}/{number:04d} - {third_party.name}"

        lines = [
            {
                "account_id": third_party.account_id,
                "description": data.description,
                "debit": total,
                "credit": Decimal("0"),
            },
            {
                "account_id": sales_account.id,
                "description": data.description,
                "debit": Decimal("0"),
                "credit": data.base_amount,
            },
            {
                "account_id": vat_account.id,
                "description": data.description,
                "debit": Decimal("0"),
                "credit": vat_amount,
            },
        ]
        if irpf_amount > 0:
            retention_account = self.account_repo.get_by_code(company_id, "4730")
            if retention_account is None:
                raise ValueError("Cuenta de retención IRPF no encontrada")
            lines.append(
                {
                    "account_id": retention_account.id,
                    "description": "Retención IRPF soportada",
                    "debit": irpf_amount,
                    "credit": Decimal("0"),
                }
            )

        entry = self.journal_service.add_accepted_entry(
            entry_date=data.date,
            description=description,
            lines=[JournalLineIn(**l) for l in lines],
            company_id=company_id,
            author_id=author_id,
        )

        invoice = Invoice(
            year=year,
            number=number,
            date=data.date,
            company_id=company_id,
            third_party_id=third_party.id,
            description=data.description,
            base_amount=data.base_amount,
            vat_rate=data.vat_rate,
            vat_amount=vat_amount,
            total=total,
            irpf_rate=data.irpf_rate,
            irpf_amount=irpf_amount,
            entry_id=entry.id,
        )
        try:
            self.invoice_repo.add(invoice)
            self.invoice_repo.commit()
        except IntegrityError:
            self.invoice_repo.rollback()
            raise ValueError(
                "No se pudo asignar el número de factura; vuelve a intentarlo"
            )
        self.invoice_repo.refresh(invoice)
        return invoice

    def list_invoices(self, company_id=None, limit: int = 50, offset: int = 0):
        return self.invoice_repo.list(company_id, limit, offset)

    def pay_issued_invoice(
        self,
        invoice_id: int,
        body: InvoicePayIn,
        company_id,
        author_id: int,
    ) -> Invoice:
        invoice = self.invoice_repo.get(invoice_id)
        if invoice is None:
            raise ValueError("Factura no existe")
        if invoice.status != "pendiente":
            raise ValueError("La factura ya está pagada o cobrada")
        if body.status.strip().lower() != "cobrada":
            raise ValueError("Estado no válido para factura emitida")
        treasury_account = self._get_treasury_account(company_id)
        if treasury_account is None:
            raise ValueError("No existe una cuenta de tesorería")

        self.journal_service.add_accepted_entry(
            entry_date=invoice.date,
            description=f"Cobro factura {invoice.year}/{invoice.number:04d}",
            lines=[
                JournalLineIn(
                    account_id=treasury_account.id,
                    description="Cobro factura",
                    debit=invoice.total,
                    credit=Decimal("0"),
                ),
                JournalLineIn(
                    account_id=invoice.third_party.account_id,
                    description="Cobro factura",
                    debit=Decimal("0"),
                    credit=invoice.total,
                ),
            ],
            company_id=company_id,
            author_id=author_id,
        )

        invoice.status = "cobrada"
        self.invoice_repo.db.add(invoice)
        self.invoice_repo.commit()
        self.invoice_repo.refresh(invoice)
        return invoice

    def _get_treasury_account(self, company_id):
        q = self.invoice_repo.db.query(Account).filter(
            Account.type == "Activo",
            Account.is_detail == True,
            Account.code.like("57%"),
        )
        if company_id is not None:
            q = q.filter(Account.company_id == company_id)
        return q.first()
