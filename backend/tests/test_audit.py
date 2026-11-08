from app.models import JournalEntry


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    return login.json()["access_token"]


def test_audit_records_journal_entry_creation(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_debit = client.post(
        "/accounts",
        json={
            "code": "572",
            "name": "Bancos",
            "type": "Activo",
            "level": 1,
            "is_detail": True,
        },
        headers=headers,
    ).json()
    acc_credit = client.post(
        "/accounts",
        json={
            "code": "700",
            "name": "Ventas",
            "type": "Ingreso",
            "level": 1,
            "is_detail": True,
        },
        headers=headers,
    ).json()

    payload = {
        "date": "2026-01-15",
        "description": "Venta de servicios",
        "lines": [
            {"account_id": acc_debit["id"], "description": "Cobro", "debit": 100, "credit": 0},
            {"account_id": acc_credit["id"], "description": "Ingreso", "debit": 0, "credit": 100},
        ],
    }
    post = client.post("/journal-entries", json=payload, headers=headers)
    assert post.status_code == 201
    entry_id = post.json()["id"]

    log = client.get("/audit-log", headers=headers)
    assert log.status_code == 200
    records = log.json()
    assert any(
        r["action"] == "journal_entry.create"
        and r["target_type"] == "journal_entry"
        and r["target_id"] == entry_id
        and r["user_email"] == "test@example.com"
        for r in records
    )


def test_audit_records_invoice_creation(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    accounts = {}
    for code, name, account_type in [
        ("4300", "Clientes generales", "Activo"),
        ("7000", "Ventas de mercaderías nacionales", "Ingreso"),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo"),
    ]:
        accounts[code] = client.post(
            "/accounts",
            json={
                "code": code,
                "name": name,
                "type": account_type,
                "level": 1,
                "is_detail": True,
            },
            headers=headers,
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

    payload = {
        "date": "2026-03-10",
        "client_id": third_party["id"],
        "description": "Servicios de consultoría",
        "base_amount": 100,
        "vat_rate": 21,
    }
    post = client.post("/invoices", json=payload, headers=headers)
    assert post.status_code == 201
    invoice_id = post.json()["id"]

    log = client.get("/audit-log", headers=headers)
    assert log.status_code == 200
    records = log.json()
    assert any(
        r["action"] == "invoice.create"
        and r["target_type"] == "invoice"
        and r["target_id"] == invoice_id
        and r["user_email"] == "test@example.com"
        for r in records
    )


def test_audit_records_invoice_approval(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    accounts = {}
    for code, name, account_type in [
        ("4300", "Clientes generales", "Activo"),
        ("7000", "Ventas de mercaderías nacionales", "Ingreso"),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo"),
        ("5700", "Bancos", "Activo"),
    ]:
        accounts[code] = client.post(
            "/accounts",
            json={
                "code": code,
                "name": name,
                "type": account_type,
                "level": 1,
                "is_detail": True,
            },
            headers=headers,
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

    payload = {
        "date": "2026-03-10",
        "client_id": third_party["id"],
        "description": "Servicios de consultoría",
        "base_amount": 100,
        "vat_rate": 21,
    }
    post = client.post("/invoices", json=payload, headers=headers)
    assert post.status_code == 201
    invoice_id = post.json()["id"]

    paid = client.post(
        f"/invoices/{invoice_id}/pay",
        json={"status": "cobrada"},
        headers=headers,
    )
    assert paid.status_code == 200

    log = client.get("/audit-log", headers=headers)
    assert log.status_code == 200
    records = log.json()
    assert any(
        r["action"] == "invoice.pay"
        and r["target_type"] == "invoice"
        and r["target_id"] == invoice_id
        and r["user_email"] == "test@example.com"
        for r in records
    )


def test_audit_records_invoice_payment(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    accounts = {}
    for code, name, account_type in [
        ("6000", "Gastos de explotación", "Gasto"),
        ("5700", "Bancos", "Activo"),
        ("4720", "Hacienda Pública, IVA soportado 21%", "Pasivo"),
    ]:
        accounts[code] = client.post(
            "/accounts",
            json={
                "code": code,
                "name": name,
                "type": account_type,
                "level": 1,
                "is_detail": True,
            },
            headers=headers,
        ).json()
    supplier = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Uno SL",
            "tax_id": "B87654321",
            "type": "proveedor",
            "account_id": accounts["6000"]["id"],
        },
        headers=headers,
    ).json()

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
    invoice_id = post.json()["id"]

    paid = client.post(
        f"/received-invoices/{invoice_id}/pay",
        json={"status": "pagada"},
        headers=headers,
    )
    assert paid.status_code == 200

    log = client.get("/audit-log", headers=headers)
    assert log.status_code == 200
    records = log.json()
    assert any(
        r["action"] == "received_invoice.pay"
        and r["target_type"] == "received_invoice"
        and r["target_id"] == invoice_id
        and r["user_email"] == "test@example.com"
        for r in records
    )


def test_audit_query_returns_author_date_detail(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc = client.post(
        "/accounts",
        json={
            "code": "572",
            "name": "Bancos",
            "type": "Activo",
            "level": 1,
            "is_detail": True,
        },
        headers=headers,
    ).json()

    payload = {
        "date": "2026-01-20",
        "description": "Cobro servicios",
        "lines": [
            {"account_id": acc["id"], "description": "Cobro", "debit": 50, "credit": 0},
            {"account_id": acc["id"], "description": "Cobro", "debit": 0, "credit": 50},
        ],
    }
    post = client.post("/journal-entries", json=payload, headers=headers)
    assert post.status_code == 201
    entry_id = post.json()["id"]

    log = client.get("/audit-log", headers=headers)
    assert log.status_code == 200
    records = log.json()
    record = next(
        r for r in records if r["target_id"] == entry_id and r["action"] == "journal_entry.create"
    )
    assert record["user_email"] == "test@example.com"
    assert record["target_type"] == "journal_entry"
    assert record["target_id"] == entry_id
    assert "created_at" in record
    assert record["created_at"] is not None
    assert record["detail"] is not None
    assert record["detail"]["description"] == "Cobro servicios"


def test_audit_record_cannot_be_modified_or_deleted(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc = client.post(
        "/accounts",
        json={
            "code": "572",
            "name": "Bancos",
            "type": "Activo",
            "level": 1,
            "is_detail": True,
        },
        headers=headers,
    ).json()

    payload = {
        "date": "2026-01-20",
        "description": "Cobro servicios",
        "lines": [
            {"account_id": acc["id"], "description": "Cobro", "debit": 50, "credit": 0},
            {"account_id": acc["id"], "description": "Cobro", "debit": 0, "credit": 50},
        ],
    }
    post = client.post("/journal-entries", json=payload, headers=headers)
    assert post.status_code == 201
    entry_id = post.json()["id"]

    log = client.get("/audit-log", headers=headers)
    assert log.status_code == 200
    records = log.json()
    record = next(
        r for r in records if r["target_id"] == entry_id and r["action"] == "journal_entry.create"
    )
    audit_id = record["id"]

    put = client.put(
        f"/audit-log/{audit_id}",
        json={"action": "modified"},
        headers=headers,
    )
    assert put.status_code == 405

    delete = client.delete(f"/audit-log/{audit_id}", headers=headers)
    assert delete.status_code == 405

    # El registro sigue intacto tras los intentos
    log2 = client.get("/audit-log", headers=headers)
    assert log2.status_code == 200
    records2 = log2.json()
    assert any(r["id"] == audit_id for r in records2)
