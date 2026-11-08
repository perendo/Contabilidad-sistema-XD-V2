TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def test_extract_pdf_bomb_final_returns_202_and_job(client):
    """Dado un PDF con bomba de descompresión, cuando se sube, entonces el sistema lo acepta para procesamiento asíncrono sin fallar."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Construir un PDF con muchas páginas vacías para simular una bomba de descompresión
    pdf_parts = [b"%PDF-1.4\n"]
    objects = []
    for i in range(1, 51):
        obj_num = i * 2
        page_num = obj_num + 1
        pdf_parts.append(f"{obj_num} 0 obj\n<< /Type /Page /Parent {page_num - 1} 0 R /MediaBox [0 0 612 792] >>\nendobj\n".encode())
        pdf_parts.append(f"{page_num} 0 obj\n<< /Type /Page /Resources << /Font << /F1 10 0 R >> >> /Contents 11 0 R >> endobj\n".encode())

    pdf_parts.append(b"10 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    pdf_parts.append(b"11 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 50 700 Td (Test) Tj ET\nendstream\nendobj\n")
    pdf_parts.append(b"12 0 obj\n<< /Type /Catalog /Pages 1 0 R >>\nendobj\n")
    pdf_parts.append(b"13 0 obj\n<< /Type /Pages /Kids [2 0 R 4 0 R 6 0 R 8 0 R 10 0 R] /Count 5 >>\nendobj\n")

    pdf_bytes = b"".join(pdf_parts)

    response = client.post(
        "/received-invoices/extract",
        files={"file": ("bomb.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "procesando"
