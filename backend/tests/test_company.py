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
