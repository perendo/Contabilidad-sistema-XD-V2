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
        json={"email": TEST_EMAIL, "password": "wrong"},
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

