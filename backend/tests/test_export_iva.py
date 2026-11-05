TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup(client, headers):
    codes = [
        ("7000", "Ventas de mercaderías nacionales", "Ingreso", True),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo", True),
        ("4300", "Clientes generales", "Activo", True),
        ("4720", "Hacienda Pública, IVA soportado 21%", "Activo", True),
        ("4721", "Hacienda Pública, IVA soportado 10%", "Activo", True),
        ("4722", "Hacienda Pública, IVA soportado 4%", "Activo", True),
        ("4723", "Hacienda Pública, IVA soportado 0%", "Activo", True),
        ("6000", "Compras de mercaderías generales", "Gasto", True),
        ("4000", "Proveedores habituales", "Pasivo", True),
    ]
    accounts = {}
    for code, name, account_type, is_detail in codes:
        payload = {"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": is_detail}
        accounts[code] = client.post("/accounts", json=payload, headers=headers).json()

    cliente = client.post(
        "/third-parties",
        json={"name": "Cliente Uno SL", "tax_id": "B12345678", "type": "cliente", "account_id": accounts["4300"]["id"]},
        headers=headers,
    ).json()

    proveedor = client.post(
        "/third-parties",
        json={"name": "Proveedor Uno SL", "tax_id": "B87654321", "type": "proveedor", "account_id": accounts["4000"]["id"]},
        headers=headers,
    ).json()

    client.post(
        "/invoices",
        json={"date": "2026-05-10", "client_id": cliente["id"], "description": "Servicios", "base_amount": 100, "vat_rate": 21},
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={"date": "2026-05-12", "supplier_id": proveedor["id"], "supplier_number": "F-2026-0001", "description": "Compra", "base_amount": 200, "vat_rate": 21, "expense_account_id": accounts["6000"]["id"]},
        headers=headers,
    )
    return accounts, cliente, proveedor


def test_export_iva_csv_returns_csv_file(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup(client, headers)

    response = client.get(
        "/exportar-iva",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "csv"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.content.decode("utf-8")
    assert "IVA devengado" in content
    assert "IVA deducible" in content
    assert "21" in content
    assert "21.0" in content or "21,0" in content


def test_export_iva_pdf_returns_pdf_file(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup(client, headers)

    response = client.get(
        "/exportar-iva",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "pdf"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 0


def test_export_iva_xlsx_returns_xlsx_file(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup(client, headers)

    response = client.get(
        "/exportar-iva",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "xlsx"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.content[:2] == b"PK"
    assert len(response.content) > 0


def test_export_iva_empty_period_returns_zero_totals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/exportar-iva",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "csv"},
        headers=headers,
    )
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "IVA devengado" in content
    assert "0" in content
    assert "neutro" in content or "a ingresar" in content or "a compensar" in content


def test_export_iva_idempotent_same_params(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup(client, headers)

    params = {"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "csv"}
    first = client.get("/exportar-iva", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/exportar-iva", params=params, headers=headers)
    assert second.status_code == 200
    assert second.content == first.content


def test_export_iva_unsupported_format_returns_400(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/exportar-iva",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "docx"},
        headers=headers,
    )
    assert response.status_code == 400
