TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _auth_headers(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_creating_a_user_allows_login(client):
    headers = _auth_headers(client)

    response = client.post(
        "/users",
        json={"email": "nuevo@example.com", "password": "clave123"},
        headers=headers,
    )
    assert response.status_code == 201

    login = client.post(
        "/auth/login",
        json={"email": "nuevo@example.com", "password": "clave123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_duplicate_email_is_rejected(client):
    headers = _auth_headers(client)

    client.post(
        "/users",
        json={"email": "dup@example.com", "password": "clave123"},
        headers=headers,
    )
    response = client.post(
        "/users",
        json={"email": "dup@example.com", "password": "otraclave"},
        headers=headers,
    )
    assert response.status_code == 409


def test_listing_users_includes_created_users(client):
    headers = _auth_headers(client)

    client.post(
        "/users",
        json={"email": "listado@example.com", "password": "clave123"},
        headers=headers,
    )

    response = client.get("/users", headers=headers)
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "listado@example.com" in emails
    assert all("password_hash" not in u for u in response.json())


def test_reject_weak_password_registration(client):
    """Dado un usuario autenticado, cuando intenta crear un usuario con contraseña corta (< 8 chars),
    entonces el sistema rechaza con 400."""
    headers = _auth_headers(client)

    response = client.post(
        "/users",
        json={"email": "corto@example.com", "password": "abc"},
        headers=headers,
    )
    assert response.status_code == 400

    # El usuario no debe haberse creado
    response = client.get("/users", headers=headers)
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "corto@example.com" not in emails


def test_reject_weak_password_login(client):
    """Dado un usuario autenticado, cuando intenta iniciar sesión con contraseña corta (< 8 chars),
    entonces el sistema rechaza con 400."""
    headers = _auth_headers(client)

    response = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": "abc"},
    )
    assert response.status_code == 400


def test_list_users_paginates_with_limit_and_offset(client):
    headers = _auth_headers(client)

    for index in (1, 2, 3):
        created = client.post(
            "/users",
            json={"email": f"pag{index}@example.com", "password": "clave123"},
            headers=headers,
        )
        assert created.status_code == 201

    first_page = client.get(
        "/users", params={"limit": 2, "offset": 0}, headers=headers
    ).json()
    second_page = client.get(
        "/users", params={"limit": 2, "offset": 2}, headers=headers
    ).json()

    assert [user["email"] for user in first_page] == [TEST_EMAIL, "pag1@example.com"]
    assert [user["email"] for user in second_page] == [
        "pag2@example.com",
        "pag3@example.com",
    ]
