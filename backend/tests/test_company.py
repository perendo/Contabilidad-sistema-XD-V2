TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def test_create_company_data_persists_and_returns(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
    }
    put = client.put("/company", json=payload, headers=headers)
    assert put.status_code in (200, 201)

    get = client.get("/company", headers=headers)
    assert get.status_code == 200
    data = get.json()
    assert data["name"] == payload["name"]
    assert data["tax_id"] == payload["tax_id"]
    assert data["address"] == payload["address"]
    assert data["fiscal_year"] == payload["fiscal_year"]

    # PGC base should be seeded automatically
    accs = client.get("/accounts", headers=headers)
    assert accs.status_code == 200
    assert len(accs.json()) >= 20

    suspense = next(a for a in accs.json() if a["code"] == "555")
    assert suspense["name"] == "Partidas pendientes de aplicación"
    assert suspense["type"] == "Activo"
    assert suspense["is_detail"] is True


def test_company_save_approval_threshold_returns_it(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "5000.00",
    }
    put = client.put("/company", json=payload, headers=headers)
    assert put.status_code == 200
    assert put.json()["approval_threshold"] == "5000.00"

    get = client.get("/company", headers=headers)
    assert get.status_code == 200
    assert get.json()["approval_threshold"] == "5000.00"


def test_company_rejects_invalid_approval_threshold(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "0",
    }
    put = client.put("/company", json=payload, headers=headers)
    assert put.status_code == 400

    get = client.get("/company", headers=headers)
    assert get.status_code == 200
    assert get.json()["approval_threshold"] is None


def test_update_company_does_not_reseed_pgc_when_accounts_exist(client, monkeypatch):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
    }
    first = client.put("/company", json=payload, headers=headers)
    assert first.status_code == 200

    calls = []

    def fake_seed(db):
        calls.append(True)
        return 0

    monkeypatch.setattr("app.company.seed_pgc", fake_seed)

    payload["name"] = "Empresa Actualizada SL"
    second = client.put("/company", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["name"] == payload["name"]
    assert calls == []
