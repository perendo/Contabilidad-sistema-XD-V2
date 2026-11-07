
def test_extract_xml_with_xxe_returns_400(client):
    """Dado un archivo XML FacturaE con entidades externas, cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo [
        <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
    <root>&xxe;</root>
    """

    response = client.post(
        "/received-invoices/extract",
        files={"file": ("factura.xml", xml_content, "application/xml")},
        headers=headers,
    )
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0
