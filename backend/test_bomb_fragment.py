

def test_extract_pdf_bomb_returns_400(client):
    """Dado un PDF con bomba de descompresión, cuando se sube, entonces el sistema devuelve 400 sin crear asiento."""
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Crear un PDF bomba (documento con muchos objetos anidados)
    bomb_pdf = b"""%PDF-1.7
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 612 792]>>endobj
4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
5 0 obj<</Length 100>>stream
BT /F1 12 Tf 50 700 Td (Hello World) Tj ET
endstream endobj
6 0 obj<</Type/Outlines/Kids[]/Count 0>>endobj
7 0 obj<</Type/Outline/Parent 6 0 R/First 8 0 R/Last 8 0 R>>endobj
8 0 obj<</Type/Outline/Parent 6 0 R/First 9 0 R/Last 9 0 R>>endobj
9 0 obj<</Type/Outline/Parent 7 0 R/Title (Bomb)\x5c\x28A\x29>>endobj
trailer<</Root 1 0 R>>
startxref
0
%%EOF'''

    response = client.post(
        "/received-invoices/extract",
        files={"file": ("bomb.pdf", bomb_pdf, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0