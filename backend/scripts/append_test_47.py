

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
