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
    assert data["iva_devengado"] == "21.00"
    assert data["iva_deducible"] == "42.00"
    assert data["saldo"] == "-21.00"
    assert data["tipo_saldo"] == "a compensar"


def test_iva_liquidation_out_serializes_two_decimals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-05-10",
            "client_id": cliente["id"],
            "description": "Servicio con decimales",
            "base_amount": 100.5,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-05-12",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0100",
            "description": "Compra con decimales",
            "base_amount": 200.25,
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
    assert data["iva_devengado"] == "21.11"
    assert data["iva_deducible"] == "42.05"
    assert data["saldo"] == "-20.94"
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
    assert data["iva_devengado"] == "21.00"
    assert data["iva_deducible"] == "32.00"
    assert data["saldo"] == "-11.00"
    assert data["tipo_saldo"] == "a compensar"
    assert data["breakdown"] == {
        "21": {"devengado": "21.00", "deducible": "0.00"},
        "10": {"devengado": "0.00", "deducible": "20.00"},
        "4": {"devengado": "0.00", "deducible": "12.00"},
        "0": {"devengado": "0.00", "deducible": "0.00"},
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
