TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def test_create_balanced_multi_line_entry_returns_201(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_debit = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1},
        headers=headers,
    ).json()
    acc_credit = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1},
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
    data = post.json()
    assert data["date"] == "2026-01-15"
    assert data["description"] == "Venta de servicios"
    assert len(data["lines"]) == 2
    assert data["lines"][0]["debit"] == 100
    assert data["lines"][1]["credit"] == 100


def test_create_unbalanced_entry_returns_400_and_persists_nothing(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1},
        headers=headers,
    ).json()

    payload = {
        "date": "2026-01-15",
        "description": "Asiento descuadrado",
        "lines": [
            {"account_id": acc_a["id"], "description": "Debe", "debit": 100, "credit": 0},
            {"account_id": acc_b["id"], "description": "Haber", "debit": 0, "credit": 90},
        ],
    }
    post = client.post("/journal-entries", json=payload, headers=headers)
    assert post.status_code == 400

    listing = client.get("/journal-entries", headers=headers)
    assert listing.status_code == 200
    assert listing.json() == []


def test_create_entry_with_invalid_account_or_amount_returns_400(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1},
        headers=headers,
    ).json()

    # cuenta inexistente
    payload_bad_account = {
        "date": "2026-01-15",
        "description": "Cuenta inexistente",
        "lines": [
            {"account_id": 999999, "description": "Debe", "debit": 100, "credit": 0},
            {"account_id": acc["id"], "description": "Haber", "debit": 0, "credit": 100},
        ],
    }
    assert client.post("/journal-entries", json=payload_bad_account, headers=headers).status_code == 400

    # importe negativo
    payload_bad_amount = {
        "date": "2026-01-15",
        "description": "Importe negativo",
        "lines": [
            {"account_id": acc["id"], "description": "Debe", "debit": -5, "credit": 0},
            {"account_id": acc["id"], "description": "Haber", "debit": 0, "credit": -5},
        ],
    }
    assert client.post("/journal-entries", json=payload_bad_amount, headers=headers).status_code == 400


def test_list_entries_filters_by_date_range(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1},
        headers=headers,
    ).json()

    for d in ("2026-01-10", "2026-01-20", "2026-02-05"):
        client.post(
            "/journal-entries",
            json={
                "date": d,
                "description": f"Entry {d}",
                "lines": [
                    {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                    {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
                ],
            },
            headers=headers,
        )

    filtered = client.get(
        "/journal-entries?date_from=2026-01-15&date_to=2026-01-31", headers=headers
    )
    assert filtered.status_code == 200
    dates = [e["date"] for e in filtered.json()]
    assert dates == ["2026-01-20"]