TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_irpf(client, headers):
    codes = [
        ("7000", "Ventas de mercaderías nacionales", "Ingreso", True),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo", True),
        ("4300", "Clientes generales", "Activo", True),
        ("6000", "Compras de mercaderías generales", "Gasto", True),
        ("4720", "Hacienda Pública, IVA soportado 21%", "Activo", True),
        ("4000", "Proveedores habituales", "Pasivo", True),
        ("4730", "Hacienda Pública, retenciones soportadas", "Activo", True),
        ("4751", "Hacienda Pública, retenciones practicadas", "Pasivo", True),
    ]
    accounts = {}
    for code, name, account_type, is_detail in codes:
        payload = {
            "code": code,
            "name": name,
            "type": account_type,
            "level": 1,
            "is_detail": is_detail,
        }
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


def test_invoice_with_irpf_stores_percentage_and_amount(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, _ = _setup_irpf(client, headers)

    response = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente["id"],
            "description": "Servicios de consultoría",
            "base_amount": 100,
            "vat_rate": 21,
            "irpf_rate": 15,
            "irpf_amount": 15,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["irpf_rate"] == 15
    assert data["irpf_amount"] == 15


def test_received_invoice_with_irpf_stores_percentage_and_amount(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, _, proveedor = _setup_irpf(client, headers)

    response = client.post(
        "/received-invoices",
        json={
            "date": "2026-04-02",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0042",
            "description": "Compra de mercaderías",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
            "irpf_rate": 15,
            "irpf_amount": 30,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["irpf_rate"] == 15
    assert data["irpf_amount"] == 30


def test_irpf_quarterly_summary_returns_totals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_irpf(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-02-10",
            "client_id": cliente["id"],
            "description": "Servicios",
            "base_amount": 100,
            "vat_rate": 21,
            "irpf_rate": 15,
            "irpf_amount": 15,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-03-15",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0100",
            "description": "Alquiler",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
            "irpf_rate": 15,
            "irpf_amount": 30,
        },
        headers=headers,
    )

    response = client.get(
        "/irpf-summary",
        params={"year": 2026, "quarter": 1},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert data["quarter"] == 1
    assert data["modelo_111"]["base"] == 200.0
    assert data["modelo_111"]["retenciones_a_ingresar"] == 30.0
    assert data["pagos_a_cuenta_130"]["base"] == 100.0
    assert data["pagos_a_cuenta_130"]["retenciones_soportadas"] == 15.0
    assert data["facturas_emitidas_count"] == 1
    assert data["facturas_recibidas_count"] == 1


def test_irpf_quarterly_summary_idempotent(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_irpf(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-05-20",
            "client_id": cliente["id"],
            "description": "Servicios",
            "base_amount": 100,
            "vat_rate": 21,
            "irpf_rate": 15,
            "irpf_amount": 15,
        },
        headers=headers,
    )

    params = {"year": 2026, "quarter": 2}
    first = client.get("/irpf-summary", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/irpf-summary", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()


def test_irpf_summary_and_export_use_constant_queries(client, count_queries):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_irpf(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-01-10",
            "client_id": cliente["id"],
            "description": "Servicios",
            "base_amount": 100,
            "vat_rate": 21,
            "irpf_rate": 15,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-02-10",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0200",
            "description": "Alquiler",
            "base_amount": 200,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
            "irpf_rate": 15,
        },
        headers=headers,
    )

    params = {"year": 2026, "quarter": 1}

    def measure(url, **extra_params):
        with count_queries() as statements:
            response = client.get(url, params={**params, **extra_params}, headers=headers)
        assert response.status_code == 200
        return response, [statement.lower() for statement in statements]

    _, small_summary = measure("/irpf-summary")
    _, small_export = measure("/exportar-irpf", format="csv")

    for index in range(2, 6):
        client.post(
            "/invoices",
            json={
                "date": f"2026-01-{index + 10:02d}",
                "client_id": cliente["id"],
                "description": "Servicios",
                "base_amount": 100,
                "vat_rate": 21,
                "irpf_rate": 15,
            },
            headers=headers,
        )
        client.post(
            "/received-invoices",
            json={
                "date": f"2026-02-{index + 10:02d}",
                "supplier_id": proveedor["id"],
                "supplier_number": f"F-2026-02{index:02d}",
                "description": "Alquiler",
                "base_amount": 200,
                "vat_rate": 21,
                "expense_account_id": accounts["6000"]["id"],
                "irpf_rate": 15,
            },
            headers=headers,
        )

    summary_response, large_summary = measure("/irpf-summary")
    export_response, large_export = measure("/exportar-irpf", format="csv")

    assert len(large_summary) == len(small_summary)
    assert len(large_export) == len(small_export)

    for statements in (small_summary, large_summary, small_export, large_export):
        invoice_queries = [
            statement
            for statement in statements
            if "from invoices" in statement or "from received_invoices" in statement
        ]
        assert invoice_queries
        assert all("sum(" in statement and "count(" in statement for statement in invoice_queries)

    data = summary_response.json()
    assert data["modelo_111"]["base"] == 1000.0
    assert data["pagos_a_cuenta_130"]["base"] == 500.0
    content = export_response.content.decode("utf-8")
    assert "1000.0" in content
    assert "500.0" in content
