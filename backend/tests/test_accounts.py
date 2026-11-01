TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def test_create_account_with_optional_parent_persists(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"code": "100", "name": "Activo", "type": "Activo", "level": 1}
    post = client.post("/accounts", json=payload, headers=headers)
    assert post.status_code == 201
    data = post.json()
    assert data["code"] == "100"
    assert data["name"] == "Activo"
    assert data["type"] == "Activo"

    get = client.get("/accounts", headers=headers)
    assert get.status_code == 200
    assert any(a["code"] == "100" for a in get.json())


def test_duplicate_account_code_returns_409(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"code": "200", "name": "Pasivo", "type": "Pasivo", "level": 1}
    first = client.post("/accounts", json=payload, headers=headers)
    assert first.status_code == 201

    duplicate = client.post("/accounts", json=payload, headers=headers)
    assert duplicate.status_code == 409


def test_search_accounts_by_code_or_name_filters(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/accounts", json={"code": "910", "name": "Cuenta Alfa", "type": "Activo", "level": 1}, headers=headers)
    client.post("/accounts", json={"code": "920", "name": "Cuenta Beta", "type": "Pasivo", "level": 1}, headers=headers)

    by_code = client.get("/accounts?search=910", headers=headers)
    assert by_code.status_code == 200
    codes = [a["code"] for a in by_code.json()]
    assert "910" in codes
    assert "920" not in codes

    by_name = client.get("/accounts?search=Beta", headers=headers)
    assert by_name.status_code == 200
    names = [a["name"] for a in by_name.json()]
    assert "Cuenta Beta" in names
    assert "Cuenta Alfa" not in names
