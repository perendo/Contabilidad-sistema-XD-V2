TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_export(client, headers):
    accounts = {}
    codes = [
        ("572", "Bancos", "Activo"),
        ("700", "Ventas", "Ingreso"),
    ]
    for code, name, account_type in codes:
        accounts[code] = client.post(
            "/accounts",
            json={"code": code, "name": name, "type": account_type, "level": 1},
            headers=headers,
        ).json()

    client.post(
        "/journal-entries",
        json={
            "date": "2026-03-10",
            "description": "Venta",
            "lines": [
                {"account_id": accounts["572"]["id"], "description": "Banco", "debit": 100, "credit": 0},
                {"account_id": accounts["700"]["id"], "description": "Venta", "debit": 0, "credit": 100},
            ],
        },
        headers=headers,
    )
    return accounts


def test_export_balance_csv_returns_csv_file(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup_export(client, headers)

    response = client.get(
        "/exportar-balance",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "csv"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.content.decode("utf-8")
    assert "572" in content
    assert "Bancos" in content
    assert "700" in content
    assert "Ventas" in content
    assert "100" in content


def test_export_balance_pdf_returns_pdf_file(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup_export(client, headers)

    response = client.get(
        "/exportar-balance",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "pdf"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 0


def test_export_balance_xlsx_returns_xlsx_file(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup_export(client, headers)

    response = client.get(
        "/exportar-balance",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "xlsx"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.content[:2] == b"PK"
    assert len(response.content) > 0


def test_export_balance_idempotent_same_params(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _setup_export(client, headers)

    params = {"date_from": "2026-01-01", "date_to": "2026-12-31", "format": "csv"}
    first = client.get("/exportar-balance", params=params, headers=headers)
    assert first.status_code == 200
    second = client.get("/exportar-balance", params=params, headers=headers)
    assert second.status_code == 200
    assert second.content == first.content
