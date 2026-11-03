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
        ("7000", "Ventas de mercaderías nacionales", "Ingreso", False),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo", False),
        ("4300", "Clientes generales", "Activo", False),
        ("4720", "Hacienda Pública, IVA soportado 21%", "Activo", False),
        ("4721", "Hacienda Pública, IVA soportado 10%", "Activo", False),
        ("4722", "Hacienda Pública, IVA soportado 4%", "Activo", False),
        ("4723", "Hacienda Pública, IVA soportado 0%", "Activo", False),
        ("6000", "Compras de mercaderías generales", "Gasto", True),
        ("4000", "Proveedores habituales", "Pasivo", False),
    ]
    accounts = {}
    for code, name, account_type, is_detail in codes:
        payload = {"code": code, "name": name, "type": account_type, "level": 1, "is_detail": is_detail}
        accounts[code] = client.post("/accounts", json=payload, headers=headers).json()

    cliente = client.post(
        "/third-parties",
        json={
            "name": "Cliente Uno SL",
            "tax_id": "B12345678",
            "type": "cliente",
            "account_id": accounts["4300"]["id"],
        },
        headers=headers,
    ).json()

    proveedor = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Uno SL",
            "tax_id": "B87654321",
            "type": "proveedor",
            "account_id": accounts["4000"]["id"],
        },
        headers=headers,
    ).json()

    return accounts, cliente, proveedor


def test_iva_liquidation_period_totals_and_balance(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-05-10",
            "client_id": cliente["id"],
            "description": "Servicios de consultoría",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-05-12",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0001",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    response = client.get(
        "/iva-liquidation",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["iva_devengado"] == 21.0
    assert data["iva_deducible"] == 42.0
    assert data["saldo"] == -21.0
    assert data["tipo_saldo"] == "a compensar"


def test_iva_liquidation_vat_rate_breakdown(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-05-10",
            "client_id": cliente["id"],
            "description": "Servicios de consultoría",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-05-12",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0002",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 10,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-05-13",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0003",
            "description": "Compra de mercaderías",
            "base_amount": 300,
            "vat_rate": 4,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    response = client.get(
        "/iva-liquidation",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["iva_devengado"] == 21.0
    assert data["iva_deducible"] == 32.0
    assert data["saldo"] == -11.0
    assert data["tipo_saldo"] == "a compensar"
    assert data["breakdown"] == {
        "21": {"devengado": 21.0, "deducible": 0.0},
        "10": {"devengado": 0.0, "deducible": 20.0},
        "4": {"devengado": 0.0, "deducible": 12.0},
        "0": {"devengado": 0.0, "deducible": 0.0},
    }


def test_iva_liquidation_idempotent_repeat_period(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-06-01",
            "client_id": cliente["id"],
            "description": "Servicio",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-06-02",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0010",
            "description": "Compra",
            "base_amount": 50,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    params = {"date_from": "2026-01-01", "date_to": "2026-12-31"}
    first = client.get("/iva-liquidation", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/iva-liquidation", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()
