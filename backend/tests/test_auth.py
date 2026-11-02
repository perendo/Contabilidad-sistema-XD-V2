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
