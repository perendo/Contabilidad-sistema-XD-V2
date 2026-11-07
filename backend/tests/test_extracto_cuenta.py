TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_accounts(client, headers):
    accounts = {}
    for code, name, account_type in (
        ("572", "Bancos", "Activo"),
        ("7000", "Ventas de mercaderías", "Ingreso"),
    ):
        accounts[code] = client.post(
            "/accounts",
            json={
                "code": code,
                "name": name,
                "type": account_type,
                "level": 1,
                "is_detail": True,
            },
            headers=headers,
        ).json()
    return accounts


def _create_entry(client, headers, accounts, entry_date, amount, status=None):
    payload = {
        "date": entry_date,
        "description": f"Asiento {entry_date}",
        "lines": [
            {
                "account_id": accounts["572"]["id"],
                "description": "Banco",
                "debit": amount,
                "credit": 0,
            },
            {
                "account_id": accounts["7000"]["id"],
                "description": "Venta",
                "debit": 0,
                "credit": amount,
            },
        ],
    }
    if status is not None:
        payload["status"] = status
    return client.post("/journal-entries", json=payload, headers=headers)


def test_extracto_cuenta_only_includes_accepted_entries(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_accounts(client, headers)

    accepted = _create_entry(client, headers, accounts, "2026-01-10", 100)
    assert accepted.status_code == 201
    assert accepted.json()["status"] == "accepted"

    draft = _create_entry(client, headers, accounts, "2026-01-11", 50, status="draft")
    assert draft.status_code == 201
    assert draft.json()["status"] == "draft"

    pending_annul = _create_entry(client, headers, accounts, "2026-01-12", 30, status="draft")
    assert pending_annul.status_code == 201
    annulled = client.post(
        f"/journal-entries/{pending_annul.json()['id']}/annul",
        headers=headers,
    )
    assert annulled.status_code == 200
    assert annulled.json()["status"] == "annulled"

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

    assert [m["entry_id"] for m in data["movements"]] == [accepted.json()["id"]]
    assert data["total_debit"] == 100.0
    assert data["total_credit"] == 0.0
    assert data["final_balance"] == 100.0


def test_extracto_cuenta_unknown_account_returns_404(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/extracto-cuenta",
        params={"account_id": 999999},
        headers=headers,
    )
    assert response.status_code == 404


def test_extracto_cuenta_uses_constant_queries(client, count_queries):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts = _setup_accounts(client, headers)
    assert _create_entry(client, headers, accounts, "2026-01-10", 100).status_code == 201

    def measure():
        with count_queries() as statements:
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
        return response, statements

    _, small = measure()

    for index in range(1, 5):
        assert (
            _create_entry(
                client, headers, accounts, f"2026-02-{index + 10:02d}", 100 + index
            ).status_code
            == 201
        )

    response, large = measure()

    assert len(large) == len(small)
    assert len(response.json()["movements"]) == 5
