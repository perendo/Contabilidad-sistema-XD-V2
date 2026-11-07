TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def test_login_seed_valid_credentials_returns_token(client):
    response = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": "wrongpassword12345"},
    )
    assert response.status_code == 401


def test_protected_route_without_token_returns_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_oauth2_token_endpoint_accepts_form_credentials(client):
    response = client.post(
        "/auth/token",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_oauth2_token_endpoint_with_invalid_credentials_returns_401(client):
    response = client.post(
        "/auth/token",
        data={"username": TEST_EMAIL, "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_sets_httponly_cookie_and_allows_cookie_auth(client):
    response = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200

    set_cookies = response.headers.get_list("set-cookie")
    token_cookie = next(c for c in set_cookies if c.startswith("token="))
    assert "httponly" in token_cookie.lower()

    marker_cookie = next(c for c in set_cookies if c.startswith("auth_session="))
    assert "httponly" not in marker_cookie.lower()

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == TEST_EMAIL


def test_logout_clears_cookie_session(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    assert client.get("/auth/me").status_code == 200

    logout = client.post("/auth/logout")
    assert logout.status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_rate_limit_after_failed_login_attempts(client):
    """Dado un usuario que intenta iniciar sesión con contraseña incorrecta varias veces,
    entonces el sistema bloquea temporalmente el acceso tras varios intentos fallidos."""
    headers = {"Authorization": f"Bearer {TEST_EMAIL}"}

    # Intentar login con contraseña incorrecta 5 veces
    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={"email": TEST_EMAIL, "password": "wrongpassword12345"},
        )
        assert response.status_code == 401

    # El siguiente intento debería ser rechazado con 429 (Too Many Requests)
    response = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": "wrongpassword12345"},
    )
    assert response.status_code == 429

def test_constant_time_authentication_unknown_user(client):
    """Dado un usuario que intenta iniciar sesión con un email inexistente,
    entonces el tiempo de respuesta es indistinguible del caso con email válido
    (evita enumeración de usuarios)."""
    import time

    # Medir tiempo para email inexistente (10 intentos)
    start = time.time()
    for _ in range(10):
        client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword12345"},
        )
    time_unknown = time.time() - start

    # Medir tiempo para email existente con contraseña incorrecta (10 intentos)
    start = time.time()
    for _ in range(10):
        client.post(
            "/auth/login",
            json={"email": TEST_EMAIL, "password": "wrongpassword12345"},
        )
    time_known = time.time() - start

    # El tiempo debería ser similar (dentro de un factor de 2)
    assert time_unknown < time_known * 2
    assert time_known < time_unknown * 2
