import pytest

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


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
