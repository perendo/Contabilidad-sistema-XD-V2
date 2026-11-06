TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _auth_headers(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_company(client, headers, name):
    resp = client.post("/companies", json={"name": name, "tax_id": "B00000000", "address": "", "fiscal_year": "2026"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def test_data_isolated_between_companies(client):
    headers = _auth_headers(client)

    company_a = _create_company(client, headers, "Empresa A")
    company_b = _create_company(client, headers, "Empresa B")

    # work in company A
    h_a = {**headers, "X-Company-Id": str(company_a["id"])}
    acc_a = client.post(
        "/accounts",
        json={"code": "100", "name": "Cuenta A", "type": "Activo", "level": 1, "is_detail": True},
        headers=h_a,
    )
    assert acc_a.status_code == 201

    # work in company B: account 100 should not exist
    h_b = {**headers, "X-Company-Id": str(company_b["id"])}
    list_b = client.get("/accounts", headers=h_b)
    assert list_b.status_code == 200
    assert all(a["code"] != "100" for a in list_b.json())

    # create 200 in B
    acc_b = client.post(
        "/accounts",
        json={"code": "200", "name": "Cuenta B", "type": "Activo", "level": 1, "is_detail": True},
        headers=h_b,
    )
    assert acc_b.status_code == 201

    # back to A: 200 should not exist
    list_a = client.get("/accounts", headers=h_a)
    assert all(a["code"] != "200" for a in list_a.json())
    assert any(a["code"] == "100" for a in list_a.json())


def test_new_company_starts_empty(client):
    headers = _auth_headers(client)
    company = _create_company(client, headers, "Empresa Nueva")
    h = {**headers, "X-Company-Id": str(company["id"])}

    accounts = client.get("/accounts", headers=h)
    assert accounts.status_code == 200
    assert accounts.json() == []

    entries = client.get("/journal-entries", headers=h)
    assert entries.status_code == 200
    assert entries.json() == []


def test_active_company_config_matches_selected(client):
    headers = _auth_headers(client)
    company_a = _create_company(client, headers, "Empresa A")
    company_b = _create_company(client, headers, "Empresa B")

    h_a = {**headers, "X-Company-Id": str(company_a["id"])}
    h_b = {**headers, "X-Company-Id": str(company_b["id"])}

    client.put("/company", json={"name": "Empresa A", "tax_id": "A111", "address": "Calle A", "fiscal_year": "2026"}, headers=h_a)
    client.put("/company", json={"name": "Empresa B", "tax_id": "B222", "address": "Calle B", "fiscal_year": "2026"}, headers=h_b)

    get_a = client.get("/company", headers=h_a)
    assert get_a.status_code == 200
    assert get_a.json()["name"] == "Empresa A"
    assert get_a.json()["tax_id"] == "A111"

    get_b = client.get("/company", headers=h_b)
    assert get_b.status_code == 200
    assert get_b.json()["name"] == "Empresa B"
    assert get_b.json()["tax_id"] == "B222"