TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_modelo_347(client, headers):
    codes = [
        ("7000", "Ventas de mercaderías nacionales", "Ingreso", True),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo", True),
        ("4300", "Clientes generales", "Activo", True),
        ("6000", "Compras de mercaderías generales", "Gasto", True),
        ("4720", "Hacienda Pública, IVA soportado 21%", "Activo", True),
        ("4000", "Proveedores habituales", "Pasivo", True),
    ]
    accounts = {}
    for code, name, account_type, is_detail in codes:
        payload = {
            "code": code,
            "name": name,
            "type": account_type,
            "level": 1, "is_detail": True,
            "is_detail": is_detail,
        }
        accounts[code] = client.post("/accounts", json=payload, headers=headers).json()

    cliente_alto_acc = client.post(
        "/accounts",
        json={"code": "4301", "name": "Clientes alto", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    cliente_alto = client.post(
        "/third-parties",
        json={
            "name": "Cliente Alto SL",
            "tax_id": "B11111111",
            "type": "cliente",
            "account_id": cliente_alto_acc["id"],
        },
        headers=headers,
    ).json()

    cliente_bajo_acc = client.post(
        "/accounts",
        json={"code": "4302", "name": "Clientes bajo", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    cliente_bajo = client.post(
        "/third-parties",
        json={
            "name": "Cliente Bajo SL",
            "tax_id": "B22222222",
            "type": "cliente",
            "account_id": cliente_bajo_acc["id"],
        },
        headers=headers,
    ).json()

    proveedor_alto_acc = client.post(
        "/accounts",
        json={"code": "4001", "name": "Proveedores alto", "type": "Pasivo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    proveedor_alto = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Alto SL",
            "tax_id": "B33333333",
            "type": "proveedor",
            "account_id": proveedor_alto_acc["id"],
        },
        headers=headers,
    ).json()

    proveedor_bajo_acc = client.post(
        "/accounts",
        json={"code": "4002", "name": "Proveedores bajo", "type": "Pasivo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    proveedor_bajo = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Bajo SL",
            "tax_id": "B44444444",
            "type": "proveedor",
            "account_id": proveedor_bajo_acc["id"],
        },
        headers=headers,
    ).json()

    return accounts, cliente_alto, cliente_bajo, proveedor_alto, proveedor_bajo


def test_modelo_347_returns_third_parties_above_threshold(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente_alto, cliente_bajo, proveedor_alto, proveedor_bajo = _setup_modelo_347(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente_alto["id"],
            "description": "Servicios",
            "base_amount": 4000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-04-15",
            "supplier_id": proveedor_alto["id"],
            "supplier_number": "F-2026-0200",
            "description": "Compra",
            "base_amount": 4000,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )
    client.post(
        "/invoices",
        json={
            "date": "2026-05-01",
            "client_id": cliente_bajo["id"],
            "description": "Servicios",
            "base_amount": 1000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-06-01",
            "supplier_id": proveedor_bajo["id"],
            "supplier_number": "F-2026-0201",
            "description": "Compra",
            "base_amount": 1000,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    response = client.get(
        "/modelo-347",
        params={"year": 2026, "threshold": 3005.06},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert data["threshold"] == "3005.06"
    tax_ids = {item["tax_id"] for item in data["third_parties"]}
    assert cliente_alto["tax_id"] in tax_ids
    assert proveedor_alto["tax_id"] in tax_ids
    assert cliente_bajo["tax_id"] not in tax_ids
    assert proveedor_bajo["tax_id"] not in tax_ids
    assert len(data["third_parties"]) == 2


def test_modelo_347_out_serializes_two_decimals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente_alto, cliente_bajo, proveedor_alto, proveedor_bajo = _setup_modelo_347(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente_alto["id"],
            "description": "Servicios con decimales",
            "base_amount": 100.5,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-04-15",
            "supplier_id": proveedor_alto["id"],
            "supplier_number": "F-2026-0201",
            "description": "Compra con decimales",
            "base_amount": 200.25,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    response = client.get(
        "/modelo-347",
        params={"year": 2026, "threshold": 100},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["threshold"] == "100.00"
    by_tax = {item["tax_id"]: item["total_annual"] for item in data["third_parties"]}
    assert by_tax[cliente_alto["tax_id"]] == "121.61"
    assert by_tax[proveedor_alto["tax_id"]] == "242.30"


def test_modelo_347_excludes_third_parties_below_threshold(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente_alto, cliente_bajo, proveedor_alto, proveedor_bajo = _setup_modelo_347(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente_alto["id"],
            "description": "Servicios",
            "base_amount": 4000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/invoices",
        json={
            "date": "2026-04-01",
            "client_id": cliente_bajo["id"],
            "description": "Servicios",
            "base_amount": 1000,
            "vat_rate": 21,
        },
        headers=headers,
    )

    response = client.get(
        "/modelo-347",
        params={"year": 2026, "threshold": 3005.06},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    tax_ids = {item["tax_id"] for item in data["third_parties"]}
    assert cliente_alto["tax_id"] in tax_ids
    assert cliente_bajo["tax_id"] not in tax_ids
    assert len(data["third_parties"]) == 1


def test_modelo_347_idempotent_repeat_year_and_threshold(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente_alto, _, proveedor_alto, _ = _setup_modelo_347(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-07-10",
            "client_id": cliente_alto["id"],
            "description": "Servicios",
            "base_amount": 4000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-08-15",
            "supplier_id": proveedor_alto["id"],
            "supplier_number": "F-2026-0300",
            "description": "Compra",
            "base_amount": 4000,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    params = {"year": 2026, "threshold": 3005.06}
    first = client.get("/modelo-347", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/modelo-347", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()


def test_modelo_347_and_export_use_constant_queries(client, count_queries):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente_alto, _, proveedor_alto, _ = _setup_modelo_347(client, headers)
    params = {"year": 2026, "threshold": 3000}

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente_alto["id"],
            "description": "Servicios",
            "base_amount": 4000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-04-15",
            "supplier_id": proveedor_alto["id"],
            "supplier_number": "F-2026-0400",
            "description": "Compra",
            "base_amount": 4000,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    def measure(url, **extra_params):
        with count_queries() as statements:
            response = client.get(url, params={**params, **extra_params}, headers=headers)
        assert response.status_code == 200
        return response, [statement.lower() for statement in statements]

    _, small_json = measure("/modelo-347")
    _, small_export = measure("/exportar-modelo-347", format="csv")

    for index in range(1, 4):
        client.post(
            "/invoices",
            json={
                "date": f"2026-09-{index + 10:02d}",
                "client_id": cliente_alto["id"],
                "description": "Servicios",
                "base_amount": 4000,
                "vat_rate": 21,
            },
            headers=headers,
        )
        client.post(
            "/received-invoices",
            json={
                "date": f"2026-10-{index + 10:02d}",
                "supplier_id": proveedor_alto["id"],
                "supplier_number": f"F-2026-04{index:02d}",
                "description": "Compra",
                "base_amount": 4000,
                "vat_rate": 21,
                "expense_account_id": accounts["6000"]["id"],
            },
            headers=headers,
        )

    json_response, large_json = measure("/modelo-347")
    export_response, large_export = measure("/exportar-modelo-347", format="csv")

    assert len(large_json) == len(small_json)
    assert len(large_export) == len(small_export)

    for statements in (small_json, large_json, small_export, large_export):
        invoice_queries = [
            statement
            for statement in statements
            if "from invoices" in statement or "from received_invoices" in statement
        ]
        assert invoice_queries
        assert all("sum(" in statement and "group by" in statement for statement in invoice_queries)

    totals = {
        item["tax_id"]: item["total_annual"]
        for item in json_response.json()["third_parties"]
    }
    assert totals == {"B11111111": "19360.00", "B33333333": "19360.00"}
    assert "19360.0" in export_response.content.decode("utf-8")
