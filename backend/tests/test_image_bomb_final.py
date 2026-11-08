TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def test_extract_image_bomb_final2_returns_202_and_job(client):
    """Dada una imagen con bomba de descompresión, cuando se sube, entonces el sistema la acepta para procesamiento asíncrono sin fallar."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Crear imagen PNG con dimensiones muy grandes (bomba de descompresión)
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (50000, 50000), color=(255, 255, 255))
    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format="PNG")
    pdf_bytes = img_bytes_io.getvalue()

    response = client.post(
        "/received-invoices/extract",
        files={"file": ("factura.png", pdf_bytes, "image/png")},
        headers=headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "procesando"
