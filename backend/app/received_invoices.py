from datetime import date as DateType
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .invoices import ALLOWED_VAT_RATES, CENT
from .journal_entries import JournalLineIn, add_accepted_entry
from .models import Account, ReceivedInvoice, ThirdParty, User

router = APIRouter(tags=["received-invoices"])

VAT_ACCOUNT_BY_RATE = {
    Decimal("21"): "4720",
    Decimal("10"): "4721",
    Decimal("4"): "4722",
    Decimal("0"): "4723",
}


class ReceivedInvoiceIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: DateType = Field(validation_alias=AliasChoices("date", "fecha"))
    third_party_id: int = Field(
        validation_alias=AliasChoices("third_party_id", "supplier_id", "proveedor_id", "tercero_id")
    )
    supplier_number: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices(
            "supplier_number", "numero_factura", "numero_proveedor", "invoice_number"
        ),
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
    expense_account_id: int = Field(
        validation_alias=AliasChoices("expense_account_id", "cuenta_gasto_id", "account_id")
    )


class ReceivedInvoiceOut(BaseModel):
    id: int
    date: DateType
    third_party_id: int
    supplier_number: str
    description: str
    base_amount: float
    vat_rate: float
    vat_amount: float
    total: float
    expense_account_id: int
    entry_id: int | None
    status: str
    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/received-invoices", response_model=ReceivedInvoiceOut, status_code=status.HTTP_201_CREATED
)
def create_received_invoice(
    body: ReceivedInvoiceIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReceivedInvoice:
    if body.base_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La base imponible debe ser positiva",
        )
    if body.vat_rate not in ALLOWED_VAT_RATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de IVA no válido"
        )
    vat_amount = (body.base_amount * body.vat_rate / 100).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    total = body.base_amount + vat_amount
    supplier_number = body.supplier_number.strip()
    if not supplier_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de factura del proveedor es obligatorio",
        )
    supplier = db.query(ThirdParty).filter(ThirdParty.id == body.third_party_id).first()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tercero no existe")
    if supplier.type.strip().lower() != "proveedor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El tercero no es un proveedor"
        )
    expense_account = (
        db.query(Account).filter(Account.id == body.expense_account_id).first()
    )
    if expense_account is None or expense_account.type != "Gasto" or not expense_account.is_detail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de gasto no es válida",
        )
    vat_account = (
        db.query(Account)
        .filter(Account.code == VAT_ACCOUNT_BY_RATE[body.vat_rate])
        .first()
    )
    if vat_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuenta de IVA soportado no encontrada",
        )
    entry = add_accepted_entry(
        db,
        entry_date=body.date,
        description=f"Factura recibida {supplier_number} - {supplier.name}",
        lines=[
            JournalLineIn(
                account_id=expense_account.id,
                description=body.description,
                debit=body.base_amount,
            ),
            JournalLineIn(
                account_id=vat_account.id,
                description=body.description,
                debit=vat_amount,
            ),
            JournalLineIn(
                account_id=supplier.account_id,
                description=body.description,
                credit=total,
            ),
        ],
    )
    invoice = ReceivedInvoice(
        date=body.date,
        third_party_id=body.third_party_id,
        supplier_number=supplier_number,
        description=body.description,
        base_amount=body.base_amount,
        vat_rate=body.vat_rate,
        vat_amount=vat_amount,
        total=total,
        expense_account_id=body.expense_account_id,
        entry_id=entry.id,
    )
    db.add(invoice)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una factura recibida de ese proveedor con ese número",
        )
    db.refresh(invoice)
    return invoice


@router.get("/received-invoices", response_model=list[ReceivedInvoiceOut])
def list_received_invoices(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReceivedInvoice]:
    return (
        db.query(ReceivedInvoice)
        .order_by(ReceivedInvoice.date, ReceivedInvoice.id)
        .all()
    )


class ReceivedInvoicePayIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str = Field(validation_alias=AliasChoices("status", "estado"))


@router.post("/received-invoices/{invoice_id}/pay", response_model=ReceivedInvoiceOut)
def pay_received_invoice(
    invoice_id: int,
    body: ReceivedInvoicePayIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReceivedInvoice:
    invoice = db.query(ReceivedInvoice).filter(ReceivedInvoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no existe")
    if invoice.status != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La factura ya está pagada o cobrada",
        )
    if body.status.strip().lower() != "pagada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado no válido para factura recibida",
        )

    treasury_account = (
        db.query(Account)
        .filter(Account.type == "Activo", Account.is_detail == True, Account.code.like("57%"))
        .first()
    )
    if treasury_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No existe una cuenta de tesorería",
        )

    add_accepted_entry(
        db,
        entry_date=invoice.date,
        description=f"Pago factura recibida {invoice.supplier_number}",
        lines=[
            JournalLineIn(
                account_id=invoice.third_party.account_id,
                description="Pago factura recibida",
                debit=invoice.total,
            ),
            JournalLineIn(
                account_id=treasury_account.id,
                description="Pago factura recibida",
                credit=invoice.total,
            ),
        ],
    )

    invoice.status = "pagada"
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
