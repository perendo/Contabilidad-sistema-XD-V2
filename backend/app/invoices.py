from datetime import date as DateType
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .journal_entries import JournalLineIn, add_accepted_entry
from .models import Account, Invoice, ThirdParty, User

router = APIRouter(tags=["invoices"])

ALLOWED_VAT_RATES = {Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0")}
CENT = Decimal("0.01")


class InvoiceIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: DateType = Field(validation_alias=AliasChoices("date", "fecha"))
    third_party_id: int = Field(
        validation_alias=AliasChoices("third_party_id", "client_id", "cliente_id", "tercero_id")
    )
    description: str = Field(
        default="",
        max_length=500,
        validation_alias=AliasChoices("description", "concept", "concepto"),
    )
    base_amount: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        validation_alias=AliasChoices("base_amount", "base", "base_imponible"),
    )
    vat_rate: Decimal = Field(validation_alias=AliasChoices("vat_rate", "iva", "tipo_iva"))
    irpf_rate: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("irpf_rate", "retencion_irpf", "tipo_retencion"),
    )
    irpf_amount: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("irpf_amount", "importe_retencion"),
    )


class InvoiceOut(BaseModel):
    id: int
    year: int
    number: int
    date: DateType
    third_party_id: int
    description: str
    base_amount: float
    vat_rate: float
    vat_amount: float
    total: float
    irpf_rate: float | None
    irpf_amount: float | None
    entry_id: int | None
    status: str
    model_config = ConfigDict(from_attributes=True)


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    body: InvoiceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Invoice:
    third_party = db.query(ThirdParty).filter(ThirdParty.id == body.third_party_id).first()
    if third_party is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tercero no existe")
    if third_party.type.strip().lower() != "cliente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El tercero no es un cliente"
        )
    if body.base_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="La base imponible debe ser positiva"
        )
    if body.vat_rate not in ALLOWED_VAT_RATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de IVA no válido"
        )
    sales_account = (
        db.query(Account)
        .filter(Account.code == "7000", Account.company_id == company_id)
        .first()
    )
    vat_account = (
        db.query(Account).filter(Account.code == "4770", Account.company_id == company_id).first()
    )
    if sales_account is None or vat_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuentas por defecto no encontradas",
        )

    vat_amount = (body.base_amount * body.vat_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    irpf_amount = Decimal("0")
    if body.irpf_rate is not None:
        irpf_amount = (body.base_amount * body.irpf_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    elif body.irpf_amount is not None:
        irpf_amount = body.irpf_amount
    total = body.base_amount + vat_amount - irpf_amount
    year = body.date.year
    # Serializa la asignación del número por ejercicio y empresa para evitar correlativos duplicados.
    if db.bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:year, :company_id)"),
            {"year": year, "company_id": company_id},
        )
    last_number = (
        db.query(func.max(Invoice.number))
        .filter(Invoice.year == year, Invoice.company_id == company_id)
        .scalar()
    )
    number = (last_number or 0) + 1
    description = f"Factura {year}/{number:04d} - {third_party.name}"

    lines = [
        JournalLineIn(
            account_id=third_party.account_id,
            description=body.description,
            debit=total,
        ),
        JournalLineIn(
            account_id=sales_account.id,
            description=body.description,
            credit=body.base_amount,
        ),
        JournalLineIn(
            account_id=vat_account.id,
            description=body.description,
            credit=vat_amount,
        ),
    ]
    if irpf_amount > 0:
        raq = db.query(Account).filter(Account.code == "4730")
        if company_id is not None:
            raq = raq.filter(Account.company_id == company_id)
        retention_account = raq.first()
        if retention_account is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cuenta de retención IRPF no encontrada",
            )
        lines.append(
            JournalLineIn(
                account_id=retention_account.id,
                description="Retención IRPF soportada",
                debit=irpf_amount,
            )
        )

    entry = add_accepted_entry(
        db,
        entry_date=body.date,
        description=description,
        lines=lines,
        company_id=company_id,
        author_id=user.id,
    )

    invoice = Invoice(
        year=year,
        number=number,
        date=body.date,
        company_id=company_id,
        third_party_id=third_party.id,
        description=body.description,
        base_amount=body.base_amount,
        vat_rate=body.vat_rate,
        vat_amount=vat_amount,
        total=total,
        irpf_rate=body.irpf_rate,
        irpf_amount=irpf_amount,
        entry_id=entry.id,
    )
    db.add(invoice)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo asignar el número de factura; vuelve a intentarlo",
        )
    db.refresh(invoice)
    return invoice


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> list[Invoice]:
    q = db.query(Invoice)
    if company_id is not None:
        q = q.filter(Invoice.company_id == company_id)
    return q.order_by(Invoice.year, Invoice.number).offset(offset).limit(limit).all()


class InvoicePayIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str = Field(validation_alias=AliasChoices("status", "estado"))


@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceOut)
def pay_issued_invoice(
    invoice_id: int,
    body: InvoicePayIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> Invoice:
    iq = db.query(Invoice).filter(Invoice.id == invoice_id)
    # Invoice has no company_id column yet (added in a later historia); keep lookup by id.
    invoice = iq.first()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no existe")
    if invoice.status != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La factura ya está pagada o cobrada",
        )
    if body.status.strip().lower() != "cobrada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado no válido para factura emitida",
        )

    taq = db.query(Account).filter(
        Account.type == "Activo", Account.is_detail == True, Account.code.like("57%")
    )
    if company_id is not None:
        taq = taq.filter(Account.company_id == company_id)
    treasury_account = taq.first()
    if treasury_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No existe una cuenta de tesorería",
        )

    add_accepted_entry(
        db,
        entry_date=invoice.date,
        description=f"Cobro factura {invoice.year}/{invoice.number:04d}",
        lines=[
            JournalLineIn(
                account_id=treasury_account.id,
                description="Cobro factura",
                debit=invoice.total,
            ),
            JournalLineIn(
                account_id=invoice.third_party.account_id,
                description="Cobro factura",
                credit=invoice.total,
            ),
        ],
        company_id=company_id,
        author_id=user.id,
    )

    invoice.status = "cobrada"
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
