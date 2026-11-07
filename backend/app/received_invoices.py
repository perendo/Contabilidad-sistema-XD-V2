from datetime import date as DateType
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime as DateTime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .invoices import ALLOWED_VAT_RATES, CENT
from .document_storage import build_file_path, documents_root, write_document
from .journal_entries import JournalLineIn, add_accepted_entry
from .models import Account, Document, JournalEntry, ReceivedInvoice, ThirdParty, User

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
    irpf_rate: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("irpf_rate", "retencion_irpf", "tipo_retencion"),
    )
    irpf_amount: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("irpf_amount", "importe_retencion"),
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
    irpf_rate: float | None
    irpf_amount: float | None
    expense_account_id: int
    entry_id: int | None
    status: str
    model_config = ConfigDict(from_attributes=True)


class ExtractedDataOut(BaseModel):
    nif: str
    name: str
    number: str
    date: DateType
    base: float
    vat_rate: float
    vat_amount: float | None = None
    total: float | None = None
    temp_file_id: str


@router.post("/received-invoices/extract", status_code=status.HTTP_200_OK)
def extract_received_invoice(
    file: UploadFile = File(...),
    expense_account_id: int | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> ExtractedDataOut:
    content = file.file.read()
    filename = file.filename or "factura"
    media_type = (file.content_type or "").lower()
    is_pdf = filename.lower().endswith(".pdf") or media_type == "application/pdf"
    is_image = filename.lower().endswith((".png", ".jpg", ".jpeg")) or media_type in (
        "image/png",
        "image/jpeg",
    )
    if not is_pdf and not is_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten archivos PDF o imagen en la extraccion",
        )
    if is_pdf:
        text = _extract_pdf_text(content)
    else:
        text = _extract_image_text(content)
    data = _parse_invoice_text(text)

    temp_file_id = uuid4().hex
    suffix = Path(filename).suffix.lower()
    temp_path = documents_root() / "temp" / f"{temp_file_id}{suffix}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(content)
    meta = {
        "filename": filename,
        "content_type": media_type,
        "content_name": temp_path.name,
    }
    (documents_root() / "temp" / f"{temp_file_id}.meta.json").write_text(
        json.dumps(meta), encoding="utf-8"
    )

    return ExtractedDataOut(
        nif=data["nif"],
        name=data["name"],
        number=data["number"],
        date=data["date"],
        base=float(data["base"]),
        vat_rate=float(data["vat_rate"]),
        vat_amount=float(data["vat_amount"]) if data.get("vat_amount") is not None else None,
        total=float(data["total"]) if data.get("total") is not None else None,
        temp_file_id=temp_file_id,
    )


def attach_document_to_entry(db: Session, entry: JournalEntry, filename: str, content_type: str, content: bytes) -> None:
    file_path = build_file_path(db, entry, filename, content_type)
    write_document(file_path, content)
    doc = Document(
        entry_id=entry.id,
        filename=filename[:255],
        content_type=content_type,
        size=len(content),
        file_path=file_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(entry)


@router.post(
    "/received-invoices/confirm",
    response_model=ReceivedInvoiceOut,
    status_code=status.HTTP_201_CREATED,
)
def confirm_received_invoice(
    temp_file_id: str = Form(...),
    third_party_id: int = Form(...),
    supplier_number: str = Form(
        validation_alias=AliasChoices(
            "supplier_number", "numero_factura", "numero_proveedor", "invoice_number"
        )
    ),
    description: str = Form(
        default="",
        max_length=500,
        validation_alias=AliasChoices("description", "concept", "concepto"),
    ),
    base_amount: Decimal = Form(
        validation_alias=AliasChoices("base_amount", "base", "base_imponible")
    ),
    vat_rate: Decimal = Form(validation_alias=AliasChoices("vat_rate", "iva", "tipo_iva")),
    expense_account_id: int = Form(
        validation_alias=AliasChoices("expense_account_id", "cuenta_gasto_id", "account_id")
    ),
    date: DateType = Form(validation_alias=AliasChoices("date", "fecha")),
    irpf_rate: Decimal | None = Form(
        default=None, validation_alias=AliasChoices("irpf_rate", "retencion_irpf", "tipo_retencion")
    ),
    irpf_amount: Decimal | None = Form(
        default=None, validation_alias=AliasChoices("irpf_amount", "importe_retencion")
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> ReceivedInvoiceOut:
    temp_dir = documents_root() / "temp"
    meta_path = temp_dir / f"{temp_file_id}.meta.json"
    if not meta_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo temporal no encontrado o ya expirado",
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    content_name = meta["content_name"]
    content_path = temp_dir / content_name
    if not content_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo temporal no encontrado o ya expirado",
        )
    content = content_path.read_bytes()
    filename = meta["filename"]
    content_type = meta["content_type"]

    body = ReceivedInvoiceIn(
        date=date,
        third_party_id=third_party_id,
        supplier_number=supplier_number,
        description=description,
        base_amount=base_amount,
        vat_rate=vat_rate,
        expense_account_id=expense_account_id,
        irpf_rate=irpf_rate,
        irpf_amount=irpf_amount,
    )
    try:
        invoice = create_received_invoice(body, user, db, company_id=company_id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    entry = db.query(JournalEntry).filter(JournalEntry.id == invoice.entry_id).first()
    attach_document_to_entry(db, entry, filename, content_type, content)

    try:
        content_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
    except OSError:
        pass

    return invoice


@router.post(
    "/received-invoices", response_model=ReceivedInvoiceOut, status_code=status.HTTP_201_CREATED
)
def create_received_invoice(
    body: ReceivedInvoiceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> ReceivedInvoice:
    if body.base_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La base imponible debe ser positiva",
        )
    if body.vat_rate not in ALLOWED_VAT_RATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de IVA no vÃ¡lido"
        )
    vat_amount = (body.base_amount * body.vat_rate / 100).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    irpf_amount = Decimal("0")
    if body.irpf_rate is not None:
        irpf_amount = (body.base_amount * body.irpf_rate / 100).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
    elif body.irpf_amount is not None:
        irpf_amount = body.irpf_amount
    total = body.base_amount + vat_amount - irpf_amount
    supplier_number = body.supplier_number.strip()
    if not supplier_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nÃºmero de factura del proveedor es obligatorio",
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
            detail="La cuenta de gasto no es vÃ¡lida",
        )
    vaq = db.query(Account).filter(Account.code == VAT_ACCOUNT_BY_RATE[body.vat_rate])
    if company_id is not None:
        vaq = vaq.filter(Account.company_id == company_id)
    vat_account = vaq.first()
    if vat_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuenta de IVA soportado no encontrada",
        )
    lines = [
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
    ]
    if irpf_amount > 0:
        raq = db.query(Account).filter(Account.code == "4751")
        if company_id is not None:
            raq = raq.filter(Account.company_id == company_id)
        retention_account = raq.first()
        if retention_account is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cuenta de retenciÃ³n IRPF no encontrada",
            )
        lines.append(
            JournalLineIn(
                account_id=retention_account.id,
                description="RetenciÃ³n IRPF practicada",
                credit=irpf_amount,
            )
        )

    entry = add_accepted_entry(
        db,
        entry_date=body.date,
        description=f"Factura recibida {supplier_number} - {supplier.name}",
        lines=lines,
        company_id=company_id,
        author_id=user.id,
    )
    invoice = ReceivedInvoice(
        date=body.date,
        company_id=company_id,
        third_party_id=body.third_party_id,
        supplier_number=supplier_number,
        description=body.description,
        base_amount=body.base_amount,
        vat_rate=body.vat_rate,
        vat_amount=vat_amount,
        total=total,
        irpf_rate=body.irpf_rate,
        irpf_amount=irpf_amount,
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
            detail="Ya existe una factura recibida de ese proveedor con ese nÃºmero",
        )
    db.refresh(invoice)
    return invoice


@router.get("/received-invoices", response_model=list[ReceivedInvoiceOut])
def list_received_invoices(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> list[ReceivedInvoice]:
    q = db.query(ReceivedInvoice)
    if company_id is not None:
        q = q.filter(ReceivedInvoice.company_id == company_id)
    return q.order_by(ReceivedInvoice.date, ReceivedInvoice.id).all()


class ReceivedInvoicePayIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str = Field(validation_alias=AliasChoices("status", "estado"))


@router.post("/received-invoices/{invoice_id}/pay", response_model=ReceivedInvoiceOut)
def pay_received_invoice(
    invoice_id: int,
    body: ReceivedInvoicePayIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
) -> ReceivedInvoice:
    invoice = db.query(ReceivedInvoice).filter(ReceivedInvoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no existe")
    if invoice.status != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La factura ya estÃ¡ pagada o cobrada",
        )
    if body.status.strip().lower() != "pagada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado no vÃ¡lido para factura recibida",
        )

    treasury_account = (
        db.query(Account)
        .filter(Account.type == "Activo", Account.is_detail == True, Account.code.like("57%"))
        .first()
    )
    if treasury_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No existe una cuenta de tesorerÃ­a",
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
        company_id=company_id,
        author_id=user.id,
    )

    invoice.status = "pagada"
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


FACTURAE_NS = "http://www.facturae.es/Facturae/2014/v3.2.1"


def _text_first(root, tag_suffix):
    for node in root.iter():
        if node.tag.split("}")[-1] == tag_suffix and node.text and node.text.strip():
            return node.text.strip()
    return None


def _parse_facturae(content):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"XML invalido: {exc}")

    seller_nif = None
    for node in root.iter():
        if node.tag.split("}")[-1] == "TaxIdentificationNumber":
            if node.text and node.text.strip():
                seller_nif = node.text.strip()
                break
    seller_name = None
    for tag in ("CorporateName", "Name"):
        val = _text_first(root, tag)
        if val:
            seller_name = val
            break
    invoice_number = _text_first(root, "InvoiceNumber")
    issue_date_str = _text_first(root, "IssueDate")
    total_amount = None
    base_amount = None
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag == "TotalAmount" and node.text and node.text.strip():
            try:
                total_amount = Decimal(node.text.strip())
            except Exception:
                pass
        if tag == "TotalAmountBeforeTaxes" and node.text and node.text.strip():
            try:
                base_amount = Decimal(node.text.strip())
            except Exception:
                pass
    vat_rate = None
    vat_amount = None
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag == "TaxRate" and node.text and node.text.strip():
            try:
                vat_rate = Decimal(node.text.strip())
            except Exception:
                pass
    for node in root.iter():
        if node.tag.split("}")[-1] == "TaxAmount":
            for child in node.iter():
                if child.tag.split("}")[-1] == "TotalAmount" and child.text and child.text.strip():
                    try:
                        vat_amount = Decimal(child.text.strip())
                    except Exception:
                        pass
    if not seller_nif:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro el NIF del proveedor")
    if not invoice_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro el numero de factura")
    if not issue_date_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro la fecha de factura")
    try:
        parsed_date = DateTime.strptime(issue_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fecha de factura invalida")
    if base_amount is None or base_amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Base imponible invalida")
    if vat_rate is None:
        vat_rate = Decimal("0")
    if vat_rate not in ALLOWED_VAT_RATES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de IVA no valido")
    if vat_amount is None:
        vat_amount = (base_amount * vat_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    if not seller_name:
        seller_name = seller_nif
    return {
        "nif": seller_nif,
        "name": seller_name,
        "number": invoice_number,
        "date": parsed_date,
        "base": base_amount,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
    }


def _next_supplier_account_code(db, company_id=None):
    prefix = "4000"
    q = db.query(Account).filter(Account.code.like(prefix + "%"))
    if company_id is not None:
        q = q.filter(Account.company_id == company_id)
    existing = [a.code for a in q.all()]
    nums = []
    for code in existing:
        suffix = code[len(prefix):]
        if suffix.isdigit():
            nums.append(int(suffix))
    next_num = (max(nums) + 1) if nums else 1
    return f"{prefix}{next_num:04d}"


def _get_or_create_supplier(db, nif, name, company_id=None):
    supplier = db.query(ThirdParty).filter(ThirdParty.tax_id == nif).first()
    if supplier is not None:
        return supplier, False
    code = _next_supplier_account_code(db, company_id)
    parent = db.query(Account).filter(Account.code == "4000").first()
    account = Account(code=code, name=name, type="Pasivo", level=4, is_detail=True, parent_id=parent.id if parent else None, company_id=company_id)
    if parent is not None:
        account.level = (parent.level or 0) + 1
    db.add(account)
    db.flush()
    third = ThirdParty(account_id=account.id, name=name, tax_id=nif, type="Proveedor")
    db.add(third)
    db.flush()
    return third, True


def _extract_pdf_text(content):
    from pdfminer.high_level import extract_text

    try:
        text = extract_text(BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer el PDF: {exc}",
        )
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo extraer texto del PDF",
        )
    return text


def _extract_image_text(content):
    from PIL import Image
    from io import BytesIO

    import pytesseract

    try:
        image = Image.open(BytesIO(content))
        text = pytesseract.image_to_string(image, lang="spa")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer la imagen: {exc}",
        )
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo extraer texto de la imagen",
        )
    return text


def _parse_invoice_text(text):
    def first(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    nif = first(r"\bNIF\b[:\s]*([A-Z0-9][A-Z0-9\- ]{7,12})")
    if not nif:
        nif = first(r"\bCIF\b[:\s]*([A-Z0-9][A-Z0-9\- ]{7,12})")
    name = first(r"Proveedor[:\s]*([^\n\r]+)")
    if not name:
        name = first(r"Raz[oó]n social[:\s]*([^\n\r]+)")
    number = first(r"Factura[:\s]*([^\s\n\r]+)")
    date_str = first(r"Fecha[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})")
    base_str = first(r"Base imponible[:\s]*([0-9.,]+)")
    vat_str = first(r"IVA[^\n\r]*?([0-9]{1,2}(?:[.,][0-9]+)?)\s*%")
    total_str = first(r"Total[:\s]*([0-9.,]+)")

    if not nif:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro el NIF del proveedor")
    if not number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro el numero de factura")
    if not date_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro la fecha de factura")
    if not base_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro la base imponible")

    def parse_decimal(value):
        value = value.replace(" ", "")
        if "," in value:
            value = value.replace(".", "").replace(",", ".")
        return Decimal(value)

    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_str):
            parsed_date = DateTime.strptime(date_str, "%Y-%m-%d").date()
        else:
            parsed_date = DateTime.strptime(date_str.replace("-", "/"), "%d/%m/%Y").date() if len(date_str.split("/")[-1]) == 4 else DateTime.strptime(date_str.replace("-", "/"), "%d/%m/%y").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fecha de factura invalida")
    try:
        base_amount = parse_decimal(base_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Base imponible invalida")
    vat_rate = Decimal(vat_str.replace(",", ".")) if vat_str else Decimal("0")
    if vat_rate not in ALLOWED_VAT_RATES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de IVA no valido")
    return {
        "nif": nif.replace(" ", ""),
        "name": name,
        "number": number,
        "date": parsed_date,
        "base": base_amount,
        "vat_rate": vat_rate,
    }


def _create_from_extracted(data, content, filename, content_type, expense_account_id, db, company_id=None, user=None):
    supplier, created = _get_or_create_supplier(db, data["nif"], data["name"], company_id)

    if expense_account_id is None:
        expense = db.query(Account).filter(Account.type == "Gasto", Account.is_detail == True).first()
        if expense is None:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe cuenta de gasto")
        expense_account_id = expense.id

    body = ReceivedInvoiceIn(
        date=data["date"],
        third_party_id=supplier.id,
        supplier_number=data["number"],
        description="",
        base_amount=data["base"],
        vat_rate=data["vat_rate"],
        expense_account_id=expense_account_id,
    )
    try:
        invoice = create_received_invoice(body, user, db, company_id=company_id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    entry = db.query(JournalEntry).filter(JournalEntry.id == invoice.entry_id).first()
    attach_document_to_entry(db, entry, filename, content_type, content)

    return {
        "supplier_created": created,
        "invoice": {
            "id": invoice.id,
            "date": invoice.date.isoformat(),
            "third_party_id": invoice.third_party_id,
            "supplier_number": invoice.supplier_number,
            "description": invoice.description,
            "base_amount": float(invoice.base_amount),
            "vat_rate": float(invoice.vat_rate),
            "vat_amount": float(invoice.vat_amount),
            "total": float(invoice.total),
            "irpf_rate": float(invoice.irpf_rate) if invoice.irpf_rate is not None else None,
            "irpf_amount": float(invoice.irpf_amount) if invoice.irpf_amount is not None else None,
            "expense_account_id": invoice.expense_account_id,
            "entry_id": invoice.entry_id,
            "status": invoice.status,
        },
    }


@router.post("/received-invoices/import", status_code=status.HTTP_201_CREATED)
def import_received_invoice(
    file: UploadFile = File(...),
    expense_account_id: int | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
):
    content = file.file.read()
    filename = file.filename or "factura"
    media_type = (file.content_type or "").lower()
    is_pdf = filename.lower().endswith(".pdf") or media_type == "application/pdf"
    if is_pdf:
        data = _parse_invoice_text(_extract_pdf_text(content))
        content_type = "application/pdf"
    else:
        data = _parse_facturae(content)
        content_type = "application/xml"
    return _create_from_extracted(data, content, filename, content_type, expense_account_id, db, company_id=company_id, user=user)
