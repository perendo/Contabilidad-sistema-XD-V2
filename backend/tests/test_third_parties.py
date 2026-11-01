TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def test_create_third_party_persists(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    account = client.post(
        "/accounts",
        json={"code": "430", "name": "Clientes", "type": "Activo", "level": 1},
        headers=headers,
    ).json()

    payload = {
        "name": "Empresa Cliente SL",
        "tax_id": "B12345678",
        "type": "cliente",
        "account_id": account["id"],
        "address": "Calle Fiscal 1",
        "phone": "912345678",
        "email": "cliente@example.com",
    }
    post = client.post("/third-parties", json=payload, headers=headers)
    assert post.status_code == 201
    data = post.json()
    assert data["name"] == payload["name"]
    assert data["tax_id"] == payload["tax_id"]
    assert data["type"] == "Cliente"
    assert data["account_id"] == account["id"]
    assert data["address"] == payload["address"]


def test_list_third_parties_filters_by_type_or_name(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc1 = client.post(
        "/accounts",
        json={"code": "430", "name": "Clientes", "type": "Activo", "level": 1},
        headers=headers,
    ).json()
    acc2 = client.post(
        "/accounts",
        json={"code": "400", "name": "Proveedores", "type": "Pasivo", "level": 1},
        headers=headers,
    ).json()

    client.post(
        "/third-parties",
        json={"name": "Cliente Uno", "tax_id": "B111", "type": "cliente", "account_id": acc1["id"]},
        headers=headers,
    )
    client.post(
        "/third-parties",
        json={"name": "Proveedor Dos", "tax_id": "B222", "type": "proveedor", "account_id": acc2["id"]},
        headers=headers,
    )

    by_type = client.get("/third-parties?type=Proveedor", headers=headers)
    assert by_type.status_code == 200
    names = [t["name"] for t in by_type.json()]
    assert "Proveedor Dos" in names
    assert "Cliente Uno" not in names

    by_name = client.get("/third-parties?search=Uno", headers=headers)
    assert by_name.status_code == 200
    names = [t["name"] for t in by_name.json()]
    assert "Cliente Uno" in names
    assert "Proveedor Dos" not in names


def test_create_third_party_with_invalid_account_or_type_returns_400(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    account = client.post(
        "/accounts",
        json={"code": "430", "name": "Clientes", "type": "Activo", "level": 1},
        headers=headers,
    ).json()

    # subcuenta inexistente
    bad_account = client.post(
        "/third-parties",
        json={"name": "X", "tax_id": "B999", "type": "cliente", "account_id": 999999},
        headers=headers,
    )
    assert bad_account.status_code == 400

    # tipo no válido
    bad_type = client.post(
        "/third-parties",
        json={"name": "Y", "tax_id": "B888", "type": "empleado", "account_id": account["id"]},
        headers=headers,
    )
    assert bad_type.status_code == 400