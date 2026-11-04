TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_balance(client, headers):
    accounts = {}
    codes = [
        ("572", "Bancos", "Activo"),
        ("7000", "Ventas de mercaderías", "Ingreso"),
        ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo"),
        ("4300", "Clientes", "Activo"),
    ]
    for code, name, account_type in codes:
        accounts[code] = client.post(
            "/accounts",
            json={"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": True},
            headers=headers,
        ).json()

    return accounts


def test_balance_sumas_saldos_returns_per_account_debit_credit_balance(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_balance(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta al contado",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 121, "credit": 0},
                {"account_id": accounts["7000"]["id"], "description": "Venta", "debit": 0, "credit": 100},
                {"account_id": accounts["4770"]["id"], "description": "IVA", "debit": 0, "credit": 21},
            ],
        },
        headers=headers,
    )
    client.post(
        "/journal-entries",
        json={
            "date": "2026-04-05",
            "description": "Cobro cliente",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 200, "credit": 0},
                {"account_id": accounts["4300"]["id"], "description": "Cliente", "debit": 0, "credit": 200},
            ],
        },
        headers=headers,
    )

    response = client.get(
        "/balance-sumas-saldos",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date_from"] == "2026-01-01"
    assert data["date_to"] == "2026-12-31"

    by_code = {row["code"]: row for row in data["accounts"]}

    # Bancos: 121 + 200 = 321 debe, 0 haber, saldo 321
    assert by_code["572"]["debe"] == 321.0
    assert by_code["572"]["haber"] == 0.0
    assert by_code["572"]["saldo"] == 321.0

    # Ventas: 0 debe, 100 haber, saldo -100
    assert by_code["7000"]["debe"] == 0.0
    assert by_code["7000"]["haber"] == 100.0
    assert by_code["7000"]["saldo"] == -100.0

    # IVA repercutido: 0 debe, 21 haber, saldo -21
    assert by_code["4770"]["debe"] == 0.0
    assert by_code["4770"]["haber"] == 21.0
    assert by_code["4770"]["saldo"] == -21.0

    # Clientes: 0 debe, 200 haber, saldo -200
    assert by_code["4300"]["debe"] == 0.0
    assert by_code["4300"]["haber"] == 200.0
    assert by_code["4300"]["saldo"] == -200.0

    # Totales globales
    assert data["total_debe"] == 321.0
    assert data["total_haber"] == 321.0
    assert data["cuadrado"] is True


def test_balance_sumas_saldos_idempotent_same_params(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_balance(client, headers)

    client.post(
        "/journal-entries",
        json={
            "date": "2026-06-01",
            "description": "Entrada idem",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 50, "credit": 0},
                {"account_id": accounts["7000"]["id"], "description": "Venta", "debit": 0, "credit": 50},
            ],
        },
        headers=headers,
    )

    params = {"date_from": "2026-01-01", "date_to": "2026-12-31"}
    first = client.get("/balance-sumas-saldos", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/balance-sumas-saldos", params=params, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()
