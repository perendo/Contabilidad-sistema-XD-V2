TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


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
