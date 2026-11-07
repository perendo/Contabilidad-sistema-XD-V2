with open('tests/test_received_invoices.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_test = '''

def test_extract_pdf_bomb_returns_400(client):
    """Dado un PDF con bomba de descompresión, cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    pdf_bytes = (
        b"%PDF-1.7\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/Resources<<</Font<</F1 4 0 R>>>>/MediaBox[0 0 612 792]>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 100>>stream\n"
        b"BT /F1 12 Tf 50 700 Td (Hello World) Tj ET\n"
        b"endstream endobj\n"
        b"6 0 obj<</Type/Outlines/Kids[]/Count 0>>endobj\n"
        b"7 0 obj<</Type/Outline/Parent 6 0 R/First 8 0 R/Last 8 0 R>>endobj\n"
        b"8 0 obj<</Type/Outline/Parent 6 0 R/First 9 0 R/Last 9 0 R>>endobj\n"
        b"9 0 obj<</Type/Outline/Parent 7 0 R/Title (Bomb)\\x5c\\x28A\\x29>>endobj\n"
        b"trailer<</Root 1 0 R>>\n"
        b"startxref\n0\n%%EOF"
    )

    response = client.post(
        "/received-invoices/extract",
        files={"file": ("bomb.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0

'''

with open('tests/test_received_invoices.py', 'a', encoding='utf-8') as f:
    f.write(new_test)

print('Test appended successfully')
