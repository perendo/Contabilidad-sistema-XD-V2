TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_libro_registro(client, headers):
    codes = [
        ("7000", "Ventas de mercaderÃ­as nacionales", "Ingreso", True),
        ("4770", "Hacienda PÃºblica, IVA repercutido 21%", "Pasivo", True),
        ("4300", "Clientes generales", "Activo", True),
        ("6000", "Compras de mercaderÃ­as generales", "Gasto", True),
        ("4720", "Hacienda PÃºblica, IVA soportado 21%", "Activo", True),
        ("4000", "Proveedores habituales", "Pasivo", True),
        ("4730", "Hacienda PÃºblica, retenciones soportadas", "Activo", True),
        ("4751", "Hacienda PÃºblica, retenciones practicadas", "Pasivo", True),
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


def test_libro_registro_devuelve_emitidas_y_recibidas_con_campos_fiscales(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_libro_registro(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente["id"],
            "description": "Servicios de consultorÃ­a",
            "base_amount": 1000,
            "vat_rate": 21,
            "irpf_rate": 15,
            "irpf_amount": 150,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-04-15",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0100",
            "description": "Compra de mercaderÃ­as",
            "base_amount": 2000,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
            "irpf_rate": 15,
            "irpf_amount": 300,
        },
        headers=headers,
    )

    response = client.get(
        "/libro-registro",
        params={"year": 2026},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026

    emitidas = data["emitidas"]
    assert len(emitidas) == 1
    fila_emitida = emitidas[0]
    assert fila_emitida["date"] == "2026-03-10"
    assert fila_emitida["number"] == 1
    assert fila_emitida["third_party_tax_id"] == "B12345678"
    assert fila_emitida["third_party_name"] == "Cliente Uno SL"
    assert fila_emitida["base_amount"] == "1000.00"
    assert fila_emitida["vat_rate"] == "21.00"
    assert fila_emitida["vat_amount"] == "210.00"
    assert fila_emitida["irpf_rate"] == "15.00"
    assert fila_emitida["irpf_amount"] == "150.00"
    assert fila_emitida["total"] == "1060.00"

    recibidas = data["recibidas"]
    assert len(recibidas) == 1
    fila_recibida = recibidas[0]
    assert fila_recibida["date"] == "2026-04-15"
    assert fila_recibida["supplier_number"] == "F-2026-0100"
    assert fila_recibida["third_party_tax_id"] == "B87654321"
    assert fila_recibida["third_party_name"] == "Proveedor Uno SL"
    assert fila_recibida["base_amount"] == "2000.00"
    assert fila_recibida["vat_rate"] == "21.00"
    assert fila_recibida["vat_amount"] == "420.00"
    assert fila_recibida["irpf_rate"] == "15.00"
    assert fila_recibida["irpf_amount"] == "300.00"
    assert fila_recibida["total"] == "2120.00"


def test_libro_registro_out_serializes_two_decimals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_libro_registro(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
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
            "date": "2026-04-15",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0101",
            "description": "Compra con decimales",
            "base_amount": 200.25,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    response = client.get(
        "/libro-registro",
        params={"year": 2026},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    fila_emitida = data["emitidas"][0]
    assert fila_emitida["base_amount"] == "100.50"
    assert fila_emitida["vat_rate"] == "21.00"
    assert fila_emitida["vat_amount"] == "21.11"
    assert fila_emitida["total"] == "121.61"
    fila_recibida = data["recibidas"][0]
    assert fila_recibida["base_amount"] == "200.25"
    assert fila_recibida["vat_rate"] == "21.00"
    assert fila_recibida["vat_amount"] == "42.05"
    assert fila_recibida["total"] == "242.30"
    assert data["total_emitidas"] == "121.61"
    assert data["total_recibidas"] == "242.30"


def test_libro_registro_filtra_por_ejercicio(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_libro_registro(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente["id"],
            "description": "Servicios 2026",
            "base_amount": 1000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/invoices",
        json={
            "date": "2027-01-15",
            "client_id": cliente["id"],
            "description": "Servicios 2027",
            "base_amount": 500,
            "vat_rate": 21,
        },
        headers=headers,
    )

    response = client.get(
        "/libro-registro",
        params={"year": 2026},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert len(data["emitidas"]) == 1
    assert data["emitidas"][0]["description"] == "Servicios 2026"


def test_libro_registro_idempotente_mismo_ejercicio(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_libro_registro(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-05-20",
            "client_id": cliente["id"],
            "description": "Servicios idem",
            "base_amount": 300,
            "vat_rate": 21,
        },
        headers=headers,
    )

    params = {"year": 2026}
    first = client.get("/libro-registro", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/libro-registro", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()


def test_libro_registro_uses_constant_queries(client, count_queries):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, cliente, proveedor = _setup_libro_registro(client, headers)

    client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": cliente["id"],
            "description": "Servicios",
            "base_amount": 1000,
            "vat_rate": 21,
        },
        headers=headers,
    )
    client.post(
        "/received-invoices",
        json={
            "date": "2026-04-15",
            "supplier_id": proveedor["id"],
            "supplier_number": "F-2026-0500",
            "description": "Compra",
            "base_amount": 2000,
            "vat_rate": 21,
            "expense_account_id": accounts["6000"]["id"],
        },
        headers=headers,
    )

    def measure():
        with count_queries() as statements:
            response = client.get(
                "/libro-registro", params={"year": 2026}, headers=headers
            )
        assert response.status_code == 200
        return response, statements

    _, small = measure()

    for index in range(1, 5):
        client_account = client.post(
            "/accounts",
            json={
                "code": f"431{index}",
                "name": f"Clientes {index}",
                "type": "Activo",
                "level": 1,
                "is_detail": True,
            },
            headers=headers,
        ).json()
        extra_client = client.post(
            "/third-parties",
            json={
                "name": f"Cliente {index} SL",
                "tax_id": f"B2000000{index}",
                "type": "cliente",
                "account_id": client_account["id"],
            },
            headers=headers,
        ).json()
        supplier_account = client.post(
            "/accounts",
            json={
                "code": f"401{index}",
                "name": f"Proveedores {index}",
                "type": "Pasivo",
                "level": 1,
                "is_detail": True,
            },
            headers=headers,
        ).json()
        extra_supplier = client.post(
            "/third-parties",
            json={
                "name": f"Proveedor {index} SL",
                "tax_id": f"B3000000{index}",
                "type": "proveedor",
                "account_id": supplier_account["id"],
            },
            headers=headers,
        ).json()
        client.post(
            "/invoices",
            json={
                "date": f"2026-06-{index + 10:02d}",
                "client_id": extra_client["id"],
                "description": "Servicios",
                "base_amount": 1000,
                "vat_rate": 21,
            },
            headers=headers,
        )
        client.post(
            "/received-invoices",
            json={
                "date": f"2026-07-{index + 10:02d}",
                "supplier_id": extra_supplier["id"],
                "supplier_number": f"F-2026-05{index:02d}",
                "description": "Compra",
                "base_amount": 2000,
                "vat_rate": 21,
                "expense_account_id": accounts["6000"]["id"],
            },
            headers=headers,
        )

    response, large = measure()

    assert len(large) == len(small)
    assert len(response.json()["emitidas"]) == 5
    assert len(response.json()["recibidas"]) == 5
