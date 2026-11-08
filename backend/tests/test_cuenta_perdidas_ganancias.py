TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_pnl(client, headers):
    accounts = {}
    codes = [
        ("572", "Bancos", "Activo"),
        ("700", "Ventas", "Ingreso"),
        ("600", "Compras", "Gasto"),
        ("4770", "IVA repercutido", "Pasivo"),
    ]
    for code, name, account_type in codes:
        accounts[code] = client.post(
            "/accounts",
            json={"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": True},
            headers=headers,
        ).json()

    return accounts


def test_cuenta_perdidas_ganancias_returns_ingresos_gastos_resultado(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta de mercaderías",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-15",
            "description": "Compra de mercaderías",
            "lines": [
                {"account_id": accounts["600"]["id"], "description": "Compra", "debit": 500, "credit": 0},
                {"account_id": accounts["4770"]["id"], "description": "IVA soportado", "debit": 210, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 710},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/cuenta-perdidas-ganancias",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date_from"] == "2026-01-01"
    assert data["date_to"] == "2026-12-31"

    # Ingresos: ventas 1000 (crédito)
    assert data["total_ingresos"] == "1000.00"
    # Gastos: compras 500 (débito)
    assert data["total_gastos"] == "500.00"
    # Resultado: 1000 - 500 = 500 beneficio
    assert data["resultado"] == "500.00"
    assert data["tipo_resultado"] == "beneficio"


def test_extracto_cuenta_returns_moves_with_running_balance(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta de mercaderías",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-15",
            "description": "Compra de mercaderías",
            "lines": [
                {"account_id": accounts["600"]["id"], "description": "Compra", "debit": 500, "credit": 0},
                {"account_id": accounts["4770"]["id"], "description": "IVA soportado", "debit": 210, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 710},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/extracto-cuenta",
        params={
            "account_id": accounts["572"]["id"],
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == accounts["572"]["id"]
    assert data["date_from"] == "2026-01-01"
    assert data["date_to"] == "2026-12-31"
    assert len(data["movements"]) == 2

    # Primer movimiento: Venta 1210 debe, saldo 1210
    mov1 = data["movements"][0]
    assert mov1["date"] == "2026-03-10"
    assert mov1["debit"] == "1210.00"
    assert mov1["credit"] == "0.00"
    assert mov1["running_balance"] == "1210.00"

    # Segundo movimiento: Compra -710 haber, saldo 1210 - 710 = 500
    mov2 = data["movements"][1]
    assert mov2["date"] == "2026-03-15"
    assert mov2["debit"] == "0.00"
    assert mov2["credit"] == "710.00"
    assert mov2["running_balance"] == "500.00"


def test_cuenta_perdidas_ganancias_idempotent_same_params(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-06-01",
            "description": "Entrada idem",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 50, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 50},
            ],
        },
        headers=headers,
    )

    params = {"date_from": "2026-01-01", "date_to": "2026-12-31"}
    first = client.get("/cuenta-perdidas-ganancias", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/cuenta-perdidas-ganancias", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()


def test_cuenta_perdidas_ganancias_totals_match_line_sum(client):
    from decimal import Decimal

    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta con decimales",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210.5, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000.5},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-15",
            "description": "Compra con decimales",
            "lines": [
                {"account_id": accounts["600"]["id"], "description": "Compra", "debit": 500.25, "credit": 0},
                {"account_id": accounts["4770"]["id"], "description": "IVA soportado", "debit": 210, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 710.25},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/cuenta-perdidas-ganancias",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Ingresos: venta 1000.50 (crédito). Gastos: compra 500.25 (débito).
    # Resultado: 1000.50 - 500.25 = 500.25
    assert Decimal(data["total_ingresos"]) == Decimal("1000.50")
    assert Decimal(data["total_gastos"]) == Decimal("500.25")
    assert Decimal(data["resultado"]) == Decimal("500.25")


def test_cuenta_perdidas_ganancias_out_serializes_two_decimals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta con decimales",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210.5, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000.5},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-15",
            "description": "Compra con decimales",
            "lines": [
                {"account_id": accounts["600"]["id"], "description": "Compra", "debit": 500.25, "credit": 0},
                {"account_id": accounts["4770"]["id"], "description": "IVA soportado", "debit": 210, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 710.25},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/cuenta-perdidas-ganancias",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_ingresos"] == "1000.50"
    assert data["total_gastos"] == "500.25"
    assert data["resultado"] == "500.25"


def test_extracto_cuenta_idempotent_same_params(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-06-01",
            "description": "Entrada idem",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 50, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 50},
            ],
        },
        headers=headers,
    )

    params = {
        "account_id": accounts["572"]["id"],
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
    }
    first = client.get("/extracto-cuenta", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/extracto-cuenta", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()


def test_extracto_cuenta_out_serializes_two_decimals(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_pnl(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta con decimales",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210.5, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000.5},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/extracto-cuenta",
        params={
            "account_id": accounts["572"]["id"],
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["movements"]) == 1
    mov = data["movements"][0]
    assert mov["debit"] == "1210.50"
    assert mov["credit"] == "0.00"
    assert mov["running_balance"] == "1210.50"
    assert data["total_debit"] == "1210.50"
    assert data["total_credit"] == "0.00"
    assert data["final_balance"] == "1210.50"


def test_pyg_returns_groups_by_first_digit(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = {}
    codes = [
        ("572", "Bancos", "Activo"),
        ("700", "Ventas", "Ingreso"),
        ("600", "Compras", "Gasto"),
        ("4770", "IVA repercutido", "Pasivo"),
    ]
    for code, name, account_type in codes:
        accounts[code] = client.post(
            "/accounts",
            json={"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": True},
            headers=headers,
        ).json()

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta de mercaderías",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-15",
            "description": "Compra de mercaderías",
            "lines": [
                {"account_id": accounts["600"]["id"], "description": "Compra", "debit": 500, "credit": 0},
                {"account_id": accounts["4770"]["id"], "description": "IVA soportado", "debit": 210, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 710},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/cuenta-perdidas-ganancias",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "grupos" in data
    grupos = {g["codigo_grupo"]: g for g in data["grupos"]}
    assert "7" in grupos
    assert "6" in grupos
    assert grupos["7"]["importe"] == "1000.00"
    assert grupos["6"]["importe"] == "-500.00"


def test_pyg_includes_subtotales_pgc(client):
    from decimal import Decimal
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    accounts = {}
    codes = [
        ("572", "Bancos", "Activo"),
        ("700", "Ventas", "Ingreso"),
        ("600", "Compras", "Gasto"),
        ("4770", "IVA repercutido", "Pasivo"),
        ("520", "Intereses pagados", "Gasto"),
    ]
    for code, name, account_type in codes:
        accounts[code] = client.post(
            "/accounts",
            json={"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": True},
            headers=headers,
        ).json()

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta de mercaderías",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 1210, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 1000},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 210},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-15",
            "description": "Compra de mercaderías",
            "lines": [
                {"account_id": accounts["600"]["id"], "description": "Compra", "debit": 500, "credit": 0},
                {"account_id": accounts["4770"]["id"], "description": "IVA soportado", "debit": 210, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 710},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-20",
            "description": "Intereses bancarios",
            "lines": [
                {"account_id": accounts["520"]["id"], "description": "Gasto financiero", "debit": 200, "credit": 0},
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 0, "credit": 200},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/cuenta-perdidas-ganancias",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "resultado_explotacion" in data
    assert "resultado_financiero" in data
    assert "resultado_ejercicio" in data

    # resultado_explotacion = grupo 7 (1000) - grupo 6 (500) = 500
    assert Decimal(data["resultado_explotacion"]) == Decimal("500.00")
    # resultado_financiero = grupo 5 (-200 gasto)
    assert Decimal(data["resultado_financiero"]) == Decimal("-200.00")
    # resultado_ejercicio = 500 + (-200) = 300
    assert Decimal(data["resultado_ejercicio"]) == Decimal("300.00")

