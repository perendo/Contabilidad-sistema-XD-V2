from fastapi.testclient import TestClient

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client: TestClient):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup(client: TestClient, headers):
    accounts = {}
    for code, name, account_type in [
        ("4300", "Clientes generales", "Activo"),
        ("7000", "Ventas de mercaderías nacionales", "Ingreso"),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo"),
        ("5700", "Caja operativa central", "Activo"),
    ]:
        payload = {"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": True, "is_detail": True}
        if code == "5700":
            payload["is_detail"] = True
        accounts[code] = client.post(
            "/accounts", json=payload, headers=headers
        ).json()
    third_party = client.post(
        "/third-parties",
        json={
            "name": "Cliente Uno SL",
            "tax_id": "B12345678",
            "type": "cliente",
            "account_id": accounts["4300"]["id"],
        },
        headers=headers,
    ).json()
    return accounts, third_party


def test_mark_issued_invoice_as_paid_creates_treasury_entry(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, third_party = _setup(client, headers)

    invoice = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": third_party["id"],
            "description": "Servicios de consultoría",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    ).json()
    assert invoice["entry_id"] is not None

    pay = client.post(
        f"/invoices/{invoice['id']}/pay",
        json={"status": "cobrada"},
        headers=headers,
    )
    assert pay.status_code == 200
    data = pay.json()
    assert data["status"] == "cobrada"

    entries = client.get("/journal-entries", headers=headers).json()
    treasury_entries = [
        e for e in entries
        if any(l["account_id"] == accounts["5700"]["id"] for l in e["lines"])
    ]
    assert len(treasury_entries) == 1
    entry = treasury_entries[0]
    assert entry["status"] == "accepted"
    lines = {(l["account_id"], l["debit"], l["credit"]) for l in entry["lines"]}
    assert (accounts["5700"]["id"], "121.00", "0.00") in lines


def _setup_received(client: TestClient, headers):
    accounts = {}
    for code, name, account_type, detail in [
        ("4000", "Proveedores habituales", "Pasivo", True),
        ("6000", "Compras de mercaderías generales", "Gasto", True),
        ("4720", "Hacienda Pública, IVA soportado 21%", "Activo", True),
        ("5700", "Caja operativa central", "Activo", True),
    ]:
        payload = {"code": code, "name": name, "type": account_type, "level": 1, "is_detail": detail}
        accounts[code] = client.post(
            "/accounts", json=payload, headers=headers
        ).json()
    supplier = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Uno SL",
            "tax_id": "B87654321",
            "type": "proveedor",
            "account_id": accounts["4000"]["id"],
        },
        headers=headers,
    ).json()
    return accounts, supplier


def test_mark_received_invoice_as_paid_creates_treasury_entry(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, supplier = _setup_received(client, headers)

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

    pay = client.post(
        f"/received-invoices/{invoice['id']}/pay",
        json={"status": "pagada"},
        headers=headers,
    )
    assert pay.status_code == 200
    data = pay.json()
    assert data["status"] == "pagada"

    entries = client.get("/journal-entries", headers=headers).json()
    treasury_entries = [
        e for e in entries
        if any(l["account_id"] == accounts["5700"]["id"] for l in e["lines"])
    ]
    assert len(treasury_entries) == 1
    entry = treasury_entries[0]
    assert entry["status"] == "accepted"
    lines = {(l["account_id"], l["debit"], l["credit"]) for l in entry["lines"]}
    assert (accounts["5700"]["id"], "0.00", "242.00") in lines
    assert (accounts["4000"]["id"], "242.00", "0.00") in lines


def test_mark_already_paid_invoice_rejected(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, third_party = _setup(client, headers)

    invoice = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": third_party["id"],
            "description": "Servicios de consultoría",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    ).json()

    first = client.post(
        f"/invoices/{invoice['id']}/pay",
        json={"status": "cobrada"},
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["status"] == "cobrada"

    second = client.post(
        f"/invoices/{invoice['id']}/pay",
        json={"status": "cobrada"},
        headers=headers,
    )
    assert second.status_code == 400

    listed = client.get("/invoices", headers=headers).json()
    assert listed[0]["status"] == "cobrada"
