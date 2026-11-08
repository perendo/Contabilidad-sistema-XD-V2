TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


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
