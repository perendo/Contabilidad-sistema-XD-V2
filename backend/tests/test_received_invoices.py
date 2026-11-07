import pytest
import shutil
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import ReceivedInvoicePending

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

_tesseract_available = shutil.which("tesseract") is not None

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(settings.test_database_url, pool_pre_ping=True),
)


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


class _ExtractResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _extract(client, *, files, headers, data=None):
    """Encola la extracción y espera al trabajo para conservar la interfaz de los tests."""
    response = client.post(
        "/received-invoices/extract", files=files, headers=headers, data=data
    )
    if response.status_code != 202:
        return response
    job_id = response.json()["job_id"]
    job = client.get(f"/received-invoices/jobs/{job_id}", headers=headers)
    payload = job.json()
    if payload.get("status") == "fallido":
        return _ExtractResponse(400, {"detail": payload.get("error")})
    return _ExtractResponse(200, payload)


def _setup_accounts_and_supplier(client, headers, include_vat_accounts=True):
    accounts = {}
    codes = [
        ("4000", "Proveedores habituales", "Pasivo"),
        ("6000", "Compras de mercaderías generales", "Gasto"),
    ]
    if include_vat_accounts:
        codes += [
            ("4720", "Hacienda Pública, IVA soportado 21%", "Activo"),
            ("4721", "Hacienda Pública, IVA soportado 10%", "Activo"),
            ("4722", "Hacienda Pública, IVA soportado 4%", "Activo"),
            ("4723", "Hacienda Pública, IVA soportado 0%", "Activo"),
        ]
    for code, name, account_type in codes:
        payload = {"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True}
        if code == "6000":
            payload["is_detail"] = True
        accounts[code] = client.post(
            "/accounts",
            json=payload,
            headers=headers,
        ).json()
    supplier = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Uno SL",
            "tax_id": "B12345678",
            "type": "proveedor",
            "account_id": accounts["4000"]["id"],
        },
        headers=headers,
    ).json()
    return accounts, supplier


FACTURAE_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<fe:Facturae xmlns:fe="http://www.facturae.es/Facturae/2014/v3.2.1">
  <FileHeader>
    <SchemaVersion>3.2.1</SchemaVersion>
    <Modality>I</Modality>
    <InvoiceIssuerType>EM</InvoiceIssuerType>
  </FileHeader>
  <Parties>
    <SellerParty>
      <TaxIdentification>
        <PersonTypeCode>J</PersonTypeCode>
        <ResidenceTypeCode>R</ResidenceTypeCode>
        <TaxIdentificationNumber>B12345678</TaxIdentificationNumber>
      </TaxIdentification>
      <LegalEntity>
        <CorporateName>Proveedor Test SL</CorporateName>
      </LegalEntity>
    </SellerParty>
    <BuyerParty>
      <TaxIdentification>
        <PersonTypeCode>J</PersonTypeCode>
        <ResidenceTypeCode>R</ResidenceTypeCode>
        <TaxIdentificationNumber>A87654321</TaxIdentificationNumber>
      </TaxIdentification>
      <LegalEntity>
        <CorporateName>Empresa Compradora SL</CorporateName>
      </LegalEntity>
    </BuyerParty>
  </Parties>
  <Invoices>
    <Invoice>
      <InvoiceHeader>
        <InvoiceNumber>F-001</InvoiceNumber>
        <InvoiceDocumentType>FC</InvoiceDocumentType>
        <InvoiceClass>OO</InvoiceClass>
      </InvoiceHeader>
      <InvoiceIssueData>
        <IssueDate>2026-01-15</IssueDate>
      </InvoiceIssueData>
      <TaxesOutputs>
        <Tax>
          <TaxTypeCode>01</TaxTypeCode>
          <TaxRate>21.00</TaxRate>
          <TaxableBase>
            <TotalAmount>100.00</TotalAmount>
          </TaxableBase>
          <TaxAmount>
            <TotalAmount>21.00</TotalAmount>
          </TaxAmount>
        </Tax>
      </TaxesOutputs>
      <InvoiceTotals>
        <TotalAmount>121.00</TotalAmount>
        <TotalAmountBeforeTaxes>100.00</TotalAmountBeforeTaxes>
        <TotalTaxOutputs>21.00</TotalTaxOutputs>
      </InvoiceTotals>
      <Items>
        <InvoiceLine>
          <ItemDescription>Servicio</ItemDescription>
          <Quantity>1</Quantity>
          <UnitPriceWithoutTax>100.00</UnitPriceWithoutTax>
          <TotalCost>100.00</TotalCost>
        </InvoiceLine>
      </Items>
    </Invoice>
  </Invoices>
</fe:Facturae>
"""


def test_import_received_invoice_from_facturae_xml_creates_invoice_entry_and_attachment(client):
    # auth
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # need a gasto account and vat account
    expense = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )

    response = client.post(
        "/received-invoices/import",
        files={"file": ("factura.xml", FACTURAE_SAMPLE.encode("utf-8"), "application/xml")},
        data={"expense_account_id": str(expense["id"])},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_created"] is True
    assert data["invoice"]["status"] == "pendiente"
    assert data["invoice"]["base_amount"] == 100.0
    assert data["invoice"]["vat_rate"] == 21.0

    # entry accepted
    entries = client.get("/journal-entries", headers=headers).json()
    imported_entry = [e for e in entries if e["id"] == data["invoice"]["entry_id"]][0]
    assert imported_entry["status"] == "accepted"

    # attachment exists
    atts = client.get(f"/journal-entries/{imported_entry['id']}/attachments", headers=headers).json()
    assert len(atts) == 1


def test_import_received_invoice_from_invalid_xml_returns_400(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )

    before = client.get("/received-invoices", headers=headers).json()
    before_ids = {i["id"] for i in before}

    response = client.post(
        "/received-invoices/import",
        files={"file": ("bad.xml", b"<foo><bar/></foo>", "application/xml")},
        data={"expense_account_id": "1"},
        headers=headers,
    )
    assert response.status_code == 400

    after = client.get("/received-invoices", headers=headers).json()
    after_ids = {i["id"] for i in after}
    assert after_ids == before_ids


def test_import_received_invoice_reuses_existing_supplier(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    acc = client.post(
        "/accounts",
        json={"code": "4000", "name": "Proveedores", "type": "Pasivo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/third-parties",
        json={"name": "Proveedor Existente", "tax_id": "B12345678", "type": "Proveedor", "account_id": acc["id"]},
        headers=headers,
    )

    client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )

    expense = client.get("/accounts", headers=headers).json()
    expense_id = [a for a in expense if a["code"] == "6000"][0]["id"]

    response = client.post(
        "/received-invoices/import",
        files={"file": ("factura.xml", FACTURAE_SAMPLE.encode("utf-8"), "application/xml")},
        data={"expense_account_id": str(expense_id)},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_created"] is False


def _make_pdf(text):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in text.split("\n"):
        pdf.cell(0, 10, line, ln=True)
    return bytes(pdf.output())


def test_import_received_invoice_from_pdf_creates_invoice_entry_and_attachment(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-001\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    response = client.post(
        "/received-invoices/import",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_created"] is True
    assert data["invoice"]["base_amount"] == 100.0
    assert data["invoice"]["vat_rate"] == 21.0

    entries = client.get("/journal-entries", headers=headers).json()
    imported_entry = [e for e in entries if e["id"] == data["invoice"]["entry_id"]][0]
    assert imported_entry["status"] == "accepted"

    atts = client.get(f"/journal-entries/{imported_entry['id']}/attachments", headers=headers).json()
    assert len(atts) == 1


def test_import_received_invoice_from_pdf_without_text_returns_400(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf_bytes = bytes(pdf.output())

    before = client.get("/received-invoices", headers=headers).json()
    before_ids = {i["id"] for i in before}

    response = client.post(
        "/received-invoices/import",
        files={"file": ("vacio.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400

    after = client.get("/received-invoices", headers=headers).json()
    after_ids = {i["id"] for i in after}
    assert after_ids == before_ids


def test_import_received_invoice_from_pdf_missing_data_returns_400(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    pdf_bytes = _make_pdf("Texto sin datos de factura\n")

    before = client.get("/received-invoices", headers=headers).json()
    before_ids = {i["id"] for i in before}

    response = client.post(
        "/received-invoices/import",
        files={"file": ("sin-datos.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400

    after = client.get("/received-invoices", headers=headers).json()
    after_ids = {i["id"] for i in after}
    assert after_ids == before_ids


def test_received_invoice_generates_balanced_accepted_entry(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    invoice = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    ).json()
    assert invoice["entry_id"] is not None

    entries = client.get("/journal-entries", headers=headers).json()
    entry = [e for e in entries if e["id"] == invoice["entry_id"]][0]
    assert entry["status"] == "accepted"
    assert entry["date"] == "2026-04-02"

    lines = {(l["account_id"], l["debit"], l["credit"]) for l in entry["lines"]}
    assert lines == {
        (accounts["6000"]["id"], "200.00", "0.00"),
        (accounts["4720"]["id"], "42.00", "0.00"),
        (accounts["4000"]["id"], "0.00", "242.00"),
    }
    from decimal import Decimal
    assert sum(Decimal(l["debit"]) for l in entry["lines"]) == sum(Decimal(l["credit"]) for l in entry["lines"])


def test_create_received_invoice_saves_supplier_number_and_totals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    payload = {
        "date": "2026-04-02",
        "supplier_id": supplier["id"],
        "supplier_number": "F-2026-0042",
        "description": "Compra de mercaderías",
        "base_amount": 200,
        "vat_rate": 21,
        "expense_account_id": accounts["6000"]["id"],
    }
    post = client.post("/received-invoices", json=payload, headers=headers)
    assert post.status_code == 201
    data = post.json()
    assert data["date"] == "2026-04-02"
    assert data["third_party_id"] == supplier["id"]
    assert data["supplier_number"] == "F-2026-0042"
    assert data["description"] == "Compra de mercaderías"
    assert data["base_amount"] == 200
    assert data["vat_rate"] == 21
    assert data["vat_amount"] == 42
    assert data["total"] == 242
    assert data["expense_account_id"] == accounts["6000"]["id"]

    listing = client.get("/received-invoices", headers=headers)
    assert listing.status_code == 200
    listed = listing.json()
    assert len(listed) == 1
    assert listed[0]["id"] == data["id"]
    assert listed[0]["supplier_number"] == "F-2026-0042"
    assert listed[0]["total"] == 242


@pytest.mark.parametrize(
    "rate,account_code,expected_vat",
    [(21, "4720", 42), (10, "4721", 20), (4, "4722", 8), (0, "4723", 0)],
)
def test_received_invoice_books_vat_to_account_for_each_rate(
    client, rate, account_code, expected_vat
):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    invoice = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": rate,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    ).json()
    assert invoice["vat_amount"] == expected_vat
    assert invoice["total"] == 200 + expected_vat

    entries = client.get("/journal-entries", headers=headers).json()
    entry = [e for e in entries if e["id"] == invoice["entry_id"]][0]
    lines = {(l["account_id"], l["debit"], l["credit"]) for l in entry["lines"]}
    assert (accounts[account_code]["id"], f"{expected_vat:.2f}", "0.00") in lines


def test_received_invoice_rejects_unknown_or_non_supplier_third_party(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, _ = _setup_accounts_and_supplier(client, headers)
    client_account = client.post(
        "/accounts",
        json={"code": "4300", "name": "Clientes", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    customer = client.post(
        "/third-parties",
        json={
            "name": "Cliente Uno SL",
            "tax_id": "B87654321",
            "type": "cliente",
            "account_id": client_account["id"],
        },
        headers=headers,
    ).json()

    payload = {
        "date": "2026-04-02",
        "supplier_number": "F-2026-0042",
        "description": "Compra de mercaderías",
        "base_amount": 200,
        "vat_rate": 21,
        "expense_account_id": accounts["6000"]["id"],
    }

    unknown = client.post(
        "/received-invoices", json={**payload, "supplier_id": 999999}, headers=headers
    )
    assert unknown.status_code == 400

    not_supplier = client.post(
        "/received-invoices", json={**payload, "supplier_id": customer["id"]}, headers=headers
    )
    assert not_supplier.status_code == 400

    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_rejects_empty_supplier_number(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    post = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "   ",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )
    assert post.status_code == 400
    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_rejects_non_positive_base_or_invalid_vat_rate(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    payload = {
        "date": "2026-04-02",
        "supplier_id": supplier["id"],
        "supplier_number": "F-2026-0042",
        "description": "Compra de mercaderías",
        "base_amount": 200,
        "vat_rate": 21,
        "expense_account_id": accounts["6000"]["id"],
    }

    for base_amount in (0, -10):
        rejected = client.post(
            "/received-invoices",
            json={**payload, "base_amount": base_amount},
            headers=headers,
        )
        assert rejected.status_code == 400

    for vat_rate in (7, 12):
        rejected = client.post(
            "/received-invoices",
            json={**payload, "vat_rate": vat_rate},
            headers=headers,
        )
        assert rejected.status_code == 400

    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_rejects_non_expense_account(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)
    sales_account = client.post(
        "/accounts",
        json={"code": "7000", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True},
        headers=headers,
    ).json()

    rejected = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": sales_account["id"],
        },
        headers=headers,
    )
    assert rejected.status_code == 400
    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_rejects_duplicate_supplier_number(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    payload = {
        "date": "2026-04-02",
        "supplier_id": supplier["id"],
        "supplier_number": "F-2026-0042",
        "description": "Compra de mercaderías",
        "base_amount": 200,
        "vat_rate": 21,
        "expense_account_id": accounts["6000"]["id"],
    }
    first = client.post("/received-invoices", json=payload, headers=headers)
    assert first.status_code == 201

    duplicate = client.post("/received-invoices", json=payload, headers=headers)
    assert duplicate.status_code == 409

    assert len(client.get("/received-invoices", headers=headers).json()) == 1
    assert len(client.get("/journal-entries", headers=headers).json()) == 1


def test_received_invoice_with_missing_vat_account_returns_400_and_persists_nothing(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(
        client, headers, include_vat_accounts=False
    )

    post = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )
    assert post.status_code == 400
    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_allows_same_supplier_number_for_different_suppliers(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, first_supplier = _setup_accounts_and_supplier(client, headers)
    second_account = client.post(
        "/accounts",
        json={"code": "4001", "name": "Proveedores varios", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    second_supplier = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Dos SL",
            "tax_id": "B11223344",
            "type": "proveedor",
            "account_id": second_account["id"],
        },
        headers=headers,
    ).json()

    payload = {
        "date": "2026-04-02",
        "supplier_number": "F-2026-0042",
        "description": "Compra de mercaderías",
        "base_amount": 200,
        "vat_rate": 21,
        "expense_account_id": accounts["6000"]["id"],
    }
    for supplier in (first_supplier, second_supplier):
        created = client.post(
            "/received-invoices", json={**payload, "supplier_id": supplier["id"]}, headers=headers
        )
        assert created.status_code == 201

    assert len(client.get("/received-invoices", headers=headers).json()) == 2


def test_received_invoice_rejects_unknown_expense_account(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, supplier = _setup_accounts_and_supplier(client, headers)

    rejected = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": 999999,
        },
        headers=headers,
    )
    assert rejected.status_code == 400
    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_rounds_vat_half_up(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    created = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 0.50,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )
    assert created.status_code == 201
    data = created.json()
    assert data["vat_amount"] == 0.11
    assert data["total"] == 0.61

    entries = client.get("/journal-entries", headers=headers).json()
    entry = [e for e in entries if e["id"] == data["entry_id"]][0]
    lines = {(l["account_id"], l["debit"], l["credit"]) for l in entry["lines"]}
    assert (accounts["4720"]["id"], "0.11", "0.00") in lines


def test_received_invoice_duplicate_ignores_surrounding_spaces(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    payload = {
        "date": "2026-04-02",
        "supplier_id": supplier["id"],
        "supplier_number": "F-2026-0042",
        "description": "Compra de mercaderías",
        "base_amount": 200,
        "vat_rate": 21,
        "expense_account_id": accounts["6000"]["id"],
    }
    assert client.post("/received-invoices", json=payload, headers=headers).status_code == 201

    duplicate = client.post(
        "/received-invoices",
        json={**payload, "supplier_number": "  F-2026-0042  "},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert len(client.get("/received-invoices", headers=headers).json()) == 1


def test_received_invoice_rejects_aggregate_expense_account(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, supplier = _setup_accounts_and_supplier(client, headers)
    aggregate = client.post(
        "/accounts",
        json={"code": "600", "name": "Compras", "type": "Gasto", "level": 1, "is_detail": False},
        headers=headers,
    ).json()

    rejected = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": aggregate["id"],
        },
        headers=headers,
    )
    assert rejected.status_code == 400
    assert client.get("/received-invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_received_invoice_and_its_payment_entry_record_the_author(client):
    seed_headers = {"Authorization": f"Bearer {_login(client)}"}
    client.post(
        "/users",
        json={"email": "comprador@example.com", "password": "clave123"},
        headers=seed_headers,
    )
    author_token = client.post(
        "/auth/login",
        json={"email": "comprador@example.com", "password": "clave123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {author_token}"}

    accounts, supplier = _setup_accounts_and_supplier(client, headers)
    client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    invoice = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": supplier["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    ).json()

    entries = client.get("/journal-entries", headers=headers).json()
    invoice_entry = next(e for e in entries if e["id"] == invoice["entry_id"])
    assert invoice_entry["author"] == "comprador@example.com"

    paid = client.post(
        f"/received-invoices/{invoice['id']}/pay",
        json={"status": "pagada"},
        headers=headers,
    )
    assert paid.status_code == 200

    entries = client.get("/journal-entries", headers=headers).json()
    payment_entry = next(e for e in entries if e["id"] != invoice["entry_id"])
    assert payment_entry["author"] == "comprador@example.com"


def test_imported_received_invoice_records_the_author(client):
    seed_headers = {"Authorization": f"Bearer {_login(client)}"}
    client.post(
        "/users",
        json={"email": "importador@example.com", "password": "clave123"},
        headers=seed_headers,
    )
    author_token = client.post(
        "/auth/login",
        json={"email": "importador@example.com", "password": "clave123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {author_token}"}

    expense = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    response = client.post(
        "/received-invoices/import",
        files={"file": ("factura.xml", FACTURAE_SAMPLE.encode("utf-8"), "application/xml")},
        data={"expense_account_id": str(expense["id"])},
        headers=headers,
    )
    assert response.status_code == 201
    invoice = response.json()["invoice"]

    entries = client.get("/journal-entries", headers=headers).json()
    imported_entry = next(e for e in entries if e["id"] == invoice["entry_id"])
    assert imported_entry["author"] == "importador@example.com"


def test_extract_received_invoice_from_pdf_returns_data_without_creating_entry(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-001\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nif"] == "B12345678"
    assert data["name"] == "Proveedor Test SL"
    assert data["number"] == "F-001"
    assert data["date"] == "2026-01-15"
    assert data["base"] == 100.0
    assert data["vat_rate"] == 21.0
    assert "temp_file_id" in data

    # no se creo ni asiento ni factura
    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_extract_received_invoice_from_pdf_without_text_returns_400_and_persists_nothing(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf_bytes = bytes(pdf.output())

    response = _extract(
        client,
        files={"file": ("vacio.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400

    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_confirm_received_invoice_creates_entry_and_attachment(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4000", "name": "Proveedores", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Test SL",
            "tax_id": "B12345678",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-001\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    extract = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert extract.status_code == 200
    temp_file_id = extract.json()["temp_file_id"]

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = client.post(
        "/received-invoices/confirm",
        data={
            "temp_file_id": temp_file_id,
            "third_party_id": str(tercero["id"]),
            "supplier_number": "F-001",
            "description": "Compra de mercaderías",
            "base_amount": "100.00",
            "vat_rate": "21",
            "expense_account_id": str(gasto["id"]),
            "date": "2026-01-15",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_number"] == "F-001"
    assert data["description"] == "Compra de mercaderías"
    assert data["base_amount"] == 100.0
    assert data["vat_rate"] == 21.0
    assert data["total"] == 121.0
    assert data["entry_id"] is not None
    assert data["status"] == "pendiente"

    entry = [e for e in client.get("/journal-entries", headers=headers).json()
             if e["id"] == data["entry_id"]][0]
    assert entry["status"] == "accepted"

    atts = client.get(f"/journal-entries/{data['entry_id']}/attachments", headers=headers).json()
    assert len(atts) == 1
    assert atts[0]["filename"] == "factura.pdf"

    assert len(client.get("/journal-entries", headers=headers).json()) == len(before_entries) + 1
    assert len(client.get("/received-invoices", headers=headers).json()) == len(before_invoices) + 1


def _make_image(text):
    from PIL import Image, ImageDraw
    from io import BytesIO

    img = Image.new("RGB", (500, 250), color="white")
    d = ImageDraw.Draw(img)
    d.text((10, 10), text, fill="black")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.skipif(not _tesseract_available, reason="Tesseract OCR no instalado")
def test_extract_received_invoice_from_image_returns_data_without_creating_entry(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado 21%", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    image_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-001\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    image_bytes = _make_image(image_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.png", image_bytes, "image/png")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nif"] == "B12345678"
    assert data["name"] == "Proveedor Test SL"
    assert data["number"] == "F-001"
    assert data["date"] == "2026-01-15"
    assert data["base"] == 100.0
    assert data["vat_rate"] == 21.0
    assert "temp_file_id" in data

    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_extract_received_invoice_with_vat_inconsistency_returns_warnings_without_creating_entry(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-002\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 25.00\n"
        "Total: 125.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nif"] == "B12345678"
    assert data["base"] == 100.0
    assert data["vat_rate"] == 21.0
    assert data["vat_amount"] == 25.0
    assert len(data["warnings"]) > 0
    assert any("IVA" in w or "cuota" in w.lower() for w in data["warnings"])

    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_extract_received_invoice_with_total_inconsistency_returns_warnings_without_creating_entry(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-003\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 130.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nif"] == "B12345678"
    assert data["base"] == 100.0
    assert data["vat_rate"] == 21.0
    assert data["vat_amount"] == 21.0
    assert data["total"] == 130.0
    assert len(data["warnings"]) > 0
    assert any("total" in w.lower() for w in data["warnings"])

    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_extract_received_invoice_without_supplier_returns_warnings_without_creating_entry(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    pdf_text = (
        "Factura: F-004\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nif"] is None or data["nif"] == ""
    assert data["name"] is None or data["name"] == ""
    assert data["number"] == "F-004"
    assert data["base"] == 100.0
    assert len(data["warnings"]) > 0
    assert any("proveedor" in w.lower() for w in data["warnings"])

    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_auto_register_below_threshold_no_warnings_third_party_exists(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral de aprobación
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "10000.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    # crear cuenta de gasto, IVA y tercero existente (códigos únicos para no chocar con seed_pgc)
    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4001", "name": "Proveedores test", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Test SL",
            "tax_id": "B12345678",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6001", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4724", "name": "IVA soportado test", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-010\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auto_registered"] is True
    assert data["nif"] == "B12345678"
    assert data["base"] == 100.0
    assert data["vat_rate"] == 21.0
    assert data["total"] == 121.0
    assert data["invoice_id"] is not None
    assert data["entry_id"] is not None
    assert len(data["warnings"]) == 0

    # se creó factura y asiento aceptado
    assert len(client.get("/journal-entries", headers=headers).json()) == len(before_entries) + 1
    assert len(client.get("/received-invoices", headers=headers).json()) == len(before_invoices) + 1
    entries = client.get("/journal-entries", headers=headers).json()
    entry = [e for e in entries if e["id"] == data["entry_id"]][0]
    assert entry["status"] == "accepted"

    atts = client.get(f"/journal-entries/{data['entry_id']}/attachments", headers=headers).json()
    assert len(atts) == 1
    assert atts[0]["filename"] == "factura.pdf"


def test_no_auto_register_above_threshold(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral bajo (100.00) y factura de 121.00
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "100.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4002", "name": "Proveedores test 2", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Test SL",
            "tax_id": "B12345678",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6002", "name": "Gasto test 2", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4725", "name": "IVA soportado test 2", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-011\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auto_registered"] is False
    assert data["invoice_id"] is None
    assert data["entry_id"] is None
    assert len(data["warnings"]) == 0

    # no se creó factura ni asiento
    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_no_auto_register_with_warnings(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral alto (10000.00) pero factura con IVA inconsistente
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "10000.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4003", "name": "Proveedores test 3", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Test SL",
            "tax_id": "B12345678",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6003", "name": "Gasto test 3", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4726", "name": "IVA soportado test 3", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-012\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 25.00\n"
        "Total: 125.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auto_registered"] is False
    assert data["invoice_id"] is None
    assert data["entry_id"] is None
    assert len(data["warnings"]) > 0
    assert any("IVA" in w or "cuota" in w.lower() for w in data["warnings"])

    # no se creó factura ni asiento
    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_no_auto_register_no_threshold_configured(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # NO configurar umbral (queda None por defecto)
    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4004", "name": "Proveedores test 4", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Test SL",
            "tax_id": "B12345678",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6004", "name": "Gasto test 4", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4727", "name": "IVA soportado test 4", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Test SL\n"
        "NIF: B12345678\n"
        "Factura: F-013\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auto_registered"] is False
    assert data["invoice_id"] is None
    assert data["entry_id"] is None
    assert len(data["warnings"]) == 0

    # no se creó factura ni asiento
    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_no_auto_register_third_party_not_exists_opens_form(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral alto, pero NO crear tercero (no existe)
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "10000.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    gasto = client.post(
        "/accounts",
        json={"code": "6005", "name": "Gasto test 5", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4728", "name": "IVA soportado test 5", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Nuevo SL\n"
        "NIF: B99999999\n"
        "Factura: F-014\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()
    before_thirds = client.get("/third-parties", headers=headers).json()

    response = _extract(
        client,
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auto_registered"] is False
    assert data["invoice_id"] is None
    assert data["entry_id"] is None
    assert data["nif"] == "B99999999"
    assert data["name"] == "Proveedor Nuevo SL"
    assert len(data["warnings"]) == 0

    # no se creó factura, asiento ni tercero
    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices
    assert client.get("/third-parties", headers=headers).json() == before_thirds
def test_reject_pending_invoice_marks_rejected_no_entry(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral bajo (100.00)
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "100.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    client.post(
        "/accounts",
        json={"code": "6021", "name": "Gasto test rechazo", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4730", "name": "IVA soportado test rechazo", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Rechazo SL\n"
        "NIF: B44444444\n"
        "Factura: F-REJ-001\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    client.post(
        "/received-invoices/extract",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 1
    pending_id = pending[0]["id"]

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = client.post(
        f"/received-invoices/pending/{pending_id}/reject",
        data={"motivo": "Factura duplicada, no se aprueba"},
        headers=headers,
    )
    assert response.status_code == 200

    # el pendiente quedó marcado como rechazado
    pending_after = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending_after) == 0

    # no se creó factura ni asiento
    assert client.get("/journal-entries", headers=headers).json() == before_entries
    assert client.get("/received-invoices", headers=headers).json() == before_invoices


def test_approve_pending_invoice_records_approver_and_timestamp(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral bajo (100.00)
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "100.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    # crear cuenta de gasto, IVA y tercero existente
    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4020", "name": "Proveedores test aprobar 2", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Aprobado SL",
            "tax_id": "B77777777",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6030", "name": "Gasto test aprobar 2", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4731", "name": "IVA soportado test aprobar 2", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Aprobado SL\n"
        "NIF: B77777777\n"
        "Factura: F-APPR-002\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    client.post(
        "/received-invoices/extract",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 1
    pending_id = pending[0]["id"]

    before_entries = client.get("/journal-entries", headers=headers).json()
    before_invoices = client.get("/received-invoices", headers=headers).json()

    response = client.post(
        f"/received-invoices/pending/{pending_id}/approve",
        data={"third_party_id": str(tercero["id"]), "expense_account_id": str(gasto["id"])},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_number"] == "F-APPR-002"
    assert data["entry_id"] is not None

    # la factura fue creada en el listado de facturas recibidas
    invoices = client.get("/received-invoices", headers=headers).json()
    assert len(invoices) == len(before_invoices) + 1
    approved = [i for i in invoices if i["supplier_number"] == "F-APPR-002"][0]
    assert approved["approved_by"] == "test@example.com"
    assert approved["approved_at"] is not None


def test_approved_invoice_shows_approver_in_listing(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # crear sociedad con umbral alto (10000.00) para que la factura quede pendiente
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "10000.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    # crear cuenta de gasto, IVA y tercero existente
    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4021", "name": "Proveedores test listado", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Listado SL",
            "tax_id": "B55555555",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6031", "name": "Gasto test listado", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4732", "name": "IVA soportado test listado", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Listado SL\n"
        "NIF: B55555555\n"
        "Factura: F-LIST-001\n"
        "Fecha: 2026-02-01\n"
        "Base imponible: 10000.00\n"
        "IVA 21%: 2100.00\n"
        "Total: 12100.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    client.post(
        "/received-invoices/extract",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 1
    pending_id = pending[0]["id"]

    client.post(
        f"/received-invoices/pending/{pending_id}/approve",
        data={"third_party_id": str(tercero["id"]), "expense_account_id": str(gasto["id"])},
        headers=headers,
    )

    invoices = client.get("/received-invoices", headers=headers).json()
    factura = [i for i in invoices if i["supplier_number"] == "F-LIST-001"][0]
    assert factura["approved_by"] == "test@example.com"
    assert factura["approved_at"] is not None


def test_unapproved_invoice_has_empty_approval_fields(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # crear cuenta de gasto, IVA y tercero existente
    cuenta_4000 = client.post(
        "/accounts",
        json={"code": "4022", "name": "Proveedores test no aprobado", "type": "Pasivo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    tercero = client.post(
        "/third-parties",
        json={
            "name": "Proveedor No Aprobado SL",
            "tax_id": "B66666666",
            "type": "proveedor",
            "account_id": cuenta_4000["id"],
        },
        headers=headers,
    ).json()
    gasto = client.post(
        "/accounts",
        json={"code": "6032", "name": "Gasto test no aprobado", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA soportado test no aprobado", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    invoice_payload = {
        "date": "2026-03-01",
        "third_party_id": tercero["id"],
        "supplier_number": "F-NOAP-001",
        "description": "Factura sin aprobar",
        "base_amount": 100.00,
        "vat_rate": 21,
        "expense_account_id": gasto["id"],
    }
    response = client.post("/received-invoices", json=invoice_payload, headers=headers)
    assert response.status_code == 201

    invoices = client.get("/received-invoices", headers=headers).json()
    factura = [i for i in invoices if i["supplier_number"] == "F-NOAP-001"][0]
    assert factura["approved_by"] is None
    assert factura["approved_at"] is None
def test_pending_invoice_persists_after_logout_and_login(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral bajo (100.00)
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "100.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    # crear cuenta de gasto e IVA
    client.post(
        "/accounts",
        json={"code": "6040", "name": "Gasto test persistencia", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4734", "name": "IVA soportado test persistencia", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Persistencia SL\n"
        "NIF: B77777777\n"
        "Factura: F-PERSIST-001\n"
        "Fecha: 2026-02-01\n"
        "Base imponible: 10000.00\n"
        "IVA 21%: 2100.00\n"
        "Total: 12100.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    client.post(
        "/received-invoices/extract",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 1
    pending_id = pending[0]["id"]
    assert pending[0]["supplier_number"] == "F-PERSIST-001"

    # cerrar sesión y volver a iniciar
    logout = client.post("/auth/logout", headers=headers)
    assert logout.status_code == 204

    login2 = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    # la factura pendiente sigue visible en la bandeja
    pending_again = client.get("/received-invoices/pending", headers=headers2).json()
    assert len(pending_again) == 1
    assert pending_again[0]["id"] == pending_id
    assert pending_again[0]["supplier_number"] == "F-PERSIST-001"

    # el documento original sigue accesible
    doc = client.get(f"/received-invoices/pending/{pending_id}/document", headers=headers2)
    assert doc.status_code == 200
    assert doc.content == pdf_bytes

def test_reject_pending_invoice_stores_reason_and_excludes_from_list(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral bajo (100.00)
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "100.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    # crear cuenta de gasto e IVA
    client.post(
        "/accounts",
        json={"code": "6041", "name": "Gasto test rechazo", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4735", "name": "IVA soportado test rechazo", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Rechazo SL\n"
        "NIF: B88888888\n"
        "Factura: F-REJ-002\n"
        "Fecha: 2026-02-01\n"
        "Base imponible: 10000.00\n"
        "IVA 21%: 2100.00\n"
        "Total: 12100.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    client.post(
        "/received-invoices/extract",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 1
    pending_id = pending[0]["id"]
    assert pending[0]["supplier_number"] == "F-REJ-002"

    # rechazar con motivo
    response = client.post(
        f"/received-invoices/pending/{pending_id}/reject",
        data={"motivo": "Factura duplicada, no se aprueba"},
        headers=headers,
    )
    assert response.status_code == 200

    # la factura rechazada no aparece en la bandeja de pendientes
    pending_after = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending_after) == 0

    # no se creó asiento contable ni factura recibida
    assert client.get("/journal-entries", headers=headers).json() == []
    assert client.get("/received-invoices", headers=headers).json() == []

def test_get_pending_detail_shows_rejection_reason(client):
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # configurar sociedad con umbral bajo (100.00)
    company_payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "100.00",
    }
    client.put("/company", json=company_payload, headers=headers)

    # crear cuenta de gasto e IVA
    client.post(
        "/accounts",
        json={"code": "6042", "name": "Gasto test detalle", "type": "Gasto", "level": 1, "is_detail": True},
        headers=headers,
    )
    client.post(
        "/accounts",
        json={"code": "4736", "name": "IVA soportado test detalle", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    pdf_text = (
        "Proveedor: Proveedor Detalle SL\n"
        "NIF: B99999999\n"
        "Factura: F-DET-001\n"
        "Fecha: 2026-02-01\n"
        "Base imponible: 10000.00\n"
        "IVA 21%: 2100.00\n"
        "Total: 12100.00\n"
    )
    pdf_bytes = _make_pdf(pdf_text)

    client.post(
        "/received-invoices/extract",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 1
    pending_id = pending[0]["id"]

    # rechazar con motivo
    response = client.post(
        f"/received-invoices/pending/{pending_id}/reject",
        data={"motivo": "Factura duplicada, no se aprueba"},
        headers=headers,
    )
    assert response.status_code == 200

    # consultar el detalle de la factura rechazada y verificar el motivo
    detail = client.get(f"/received-invoices/pending/{pending_id}", headers=headers)
    assert detail.status_code == 200
    data = detail.json()
    assert data["id"] == pending_id
    assert data["supplier_number"] == "F-DET-001"
    assert data["status"] == "rechazado"
    assert data["reason"] == "Factura duplicada, no se aprueba"

def test_extract_pdf_bomb_returns_400(client):
    """Dado un PDF con bomba de descompresión, cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    pdf_bytes = b'%PDF-1.4\n1 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n2 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n4 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n7 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n8 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n9 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n10 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n11 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n12 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n13 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n14 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n15 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n16 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n17 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n18 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n19 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n20 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n21 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n22 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n23 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n24 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n25 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n26 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n27 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n28 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n29 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n30 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n31 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n32 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n33 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n34 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n35 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n36 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n37 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n38 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n39 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n40 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n41 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n42 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n43 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n44 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n45 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n46 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n47 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n48 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n49 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n50 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n51 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n52 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n53 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n54 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n55 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n56 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n57 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n58 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n59 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n60 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n61 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n62 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n63 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n64 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n65 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n66 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n67 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n68 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n69 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n70 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n71 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n72 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n73 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n74 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n75 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n76 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n77 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n78 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n79 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n80 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n81 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n82 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n83 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n84 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n85 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n86 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n87 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n88 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n89 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n90 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n91 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n92 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n93 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n94 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n95 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n96 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n97 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n98 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n99 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n100 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n101 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n102 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n103 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n104 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n105 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n106 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n107 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n108 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n109 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n110 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n111 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n112 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n113 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n114 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n115 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n116 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n117 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n118 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n119 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n120 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n121 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n122 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n123 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n124 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n125 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n126 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n127 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n128 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n129 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n130 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n131 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n132 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n133 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n134 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n135 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n136 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n137 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n138 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n139 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n140 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n141 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n142 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n143 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n144 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n145 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n146 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n147 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n148 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n149 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n150 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [1 0 R 4 0 R 7 0 R 10 0 R 13 0 R 16 0 R 19 0 R 22 0 R 25 0 R 28 0 R 31 0 R 34 0 R 37 0 R 40 0 R 43 0 R 46 0 R 49 0 R 52 0 R 55 0 R 58 0 R 61 0 R 64 0 R 67 0 R 70 0 R 73 0 R 76 0 R 79 0 R 82 0 R 85 0 R 88 0 R 91 0 R 94 0 R 97 0 R 100 0 R 103 0 R 106 0 R 109 0 R 112 0 R 115 0 R 118 0 R 121 0 R 124 0 R 127 0 R 130 0 R 133 0 R 136 0 R 139 0 R 142 0 R 145 0 R 148 0 R] /Count 50 >>\nendobj\n'

    response = _extract(
        client,
        files={"file": ("bomb.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0


def test_extract_image_bomb_returns_400(client):
    """Dada una imagen con bomba de descompresión, cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Crear imagen PNG con dimensiones muy grandes (bomba de descompresión)
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (50000, 50000), color=(255, 255, 255))
    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format="PNG")
    pdf_bytes = img_bytes_io.getvalue()

    response = _extract(
        client,
        files={"file": ("factura.png", pdf_bytes, "image/png")},
        headers=headers,
    )
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0


def test_extract_xml_with_xxe_returns_400(client):
    """Dado un archivo XML FacturaE con entidades externas, cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo [
        <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
    <root>&xxe;</root>
    """

    response = _extract(
        client,
        files={"file": ("factura.xml", xml_content, "application/xml")},
        headers=headers,
    )
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0


def _invoice_job_pdf_text(number="F-JOB-001"):
    return (
        "Proveedor: Proveedor Job SL\n"
        "NIF: B12345678\n"
        f"Factura: {number}\n"
        "Fecha: 2026-01-15\n"
        "Base imponible: 100.00\n"
        "IVA 21%: 21.00\n"
        "Total: 121.00\n"
    )


def test_extract_returns_202_with_job_id(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    response = client.post(
        "/received-invoices/extract",
        files={
            "file": (
                "factura.pdf",
                _make_pdf(_invoice_job_pdf_text()),
                "application/pdf",
            )
        },
        headers=headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "procesando"
    assert len(data["job_id"]) == 32


def test_extract_job_reports_completed_with_extracted_data(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    created = client.post(
        "/received-invoices/extract",
        files={
            "file": (
                "factura.pdf",
                _make_pdf(_invoice_job_pdf_text()),
                "application/pdf",
            )
        },
        headers=headers,
    )
    job_id = created.json()["job_id"]

    job = client.get(f"/received-invoices/jobs/{job_id}", headers=headers)

    assert job.status_code == 200
    data = job.json()
    assert data["status"] == "completado"
    assert data["nif"] == "B12345678"
    assert data["date"] == "2026-01-15"
    assert data["base"] == 100.0
    assert data["vat_rate"] == 21.0
    assert data["total"] == 121.0
    assert data["temp_file_id"]
    assert data["auto_registered"] is False
    assert data["warnings"] == []


def test_extract_job_reports_failure_with_error(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    created = client.post(
        "/received-invoices/extract",
        files={
            "file": (
                "factura.pdf",
                _make_pdf("Documento sin datos de factura"),
                "application/pdf",
            )
        },
        headers=headers,
    )
    job_id = created.json()["job_id"]

    job = client.get(f"/received-invoices/jobs/{job_id}", headers=headers)

    assert job.status_code == 200
    data = job.json()
    assert data["status"] == "fallido"
    assert data["error"]
    assert client.get("/received-invoices/pending", headers=headers).json() == []


def test_extract_job_not_found_returns_404(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    response = client.get("/received-invoices/jobs/no-existe", headers=headers)

    assert response.status_code == 404


def test_extract_job_is_isolated_by_company(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    created = client.post(
        "/received-invoices/extract",
        files={
            "file": (
                "factura.pdf",
                _make_pdf(_invoice_job_pdf_text()),
                "application/pdf",
            )
        },
        headers=headers,
    )
    job_id = created.json()["job_id"]

    other = client.post(
        "/companies",
        json={
            "name": "Otra Sociedad",
            "tax_id": "B00000002",
            "address": "",
            "fiscal_year": "2026",
        },
        headers=headers,
    )
    assert other.status_code == 201
    client.cookies.set("active_company_id", str(other.json()["id"]))

    response = client.get(f"/received-invoices/jobs/{job_id}", headers=headers)

    assert response.status_code == 404


def test_list_received_invoices_paginates_with_limit_and_offset(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_accounts_and_supplier(client, headers)

    invoice_ids = []
    for index in (1, 2, 3):
        created = client.post(
            "/received-invoices",
            json={
                "date": f"2026-05-0{index}",
                "supplier_id": supplier["id"],
                "supplier_number": f"F-PAG-{index}",
                "description": "Compra",
                "base_amount": 100,
                "vat_rate": 21,
                "expense_account_id": accounts["6000"]["id"],
            },
            headers=headers,
        ).json()
        invoice_ids.append(created["id"])

    first_page = client.get(
        "/received-invoices", params={"limit": 2, "offset": 0}, headers=headers
    ).json()
    second_page = client.get(
        "/received-invoices", params={"limit": 2, "offset": 2}, headers=headers
    ).json()

    assert [invoice["id"] for invoice in first_page] == invoice_ids[:2]
    assert [invoice["id"] for invoice in second_page] == invoice_ids[2:]


def test_list_pending_invoices_paginates_with_limit_and_offset(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    company_id = int(client.cookies.get("active_company_id"))

    db = TestingSessionLocal()
    pending_ids = []
    try:
        for index in (1, 2, 3):
            pending = ReceivedInvoicePending(
                company_id=company_id,
                supplier_number=f"F-PEND-{index}",
                date=date(2026, 5, index),
                base_amount=Decimal("100"),
                vat_rate=Decimal("21"),
                status="pendiente",
                file_path="",
                filename="",
                created_at=datetime(2026, 1, 1, 12, 0, index),
            )
            db.add(pending)
            db.flush()
            pending_ids.append(pending.id)
        db.commit()
    finally:
        db.close()

    first_page = client.get(
        "/received-invoices/pending", params={"limit": 2, "offset": 0}, headers=headers
    ).json()
    second_page = client.get(
        "/received-invoices/pending", params={"limit": 2, "offset": 2}, headers=headers
    ).json()

    assert [invoice["id"] for invoice in first_page] == pending_ids[::-1][:2]
    assert [invoice["id"] for invoice in second_page] == pending_ids[::-1][2:]
