# Script para agregar el test de imagen bomba al final del archivo de tests

test_code = r'''
def test_extract_image_bomb_returns_400(client):
    """Dada una imagen con bomba de descompresión, cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura."""
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
    assert response.status_code == 400

    # No se debe crear entrada en la bandeja de pendientes
    pending = client.get("/received-invoices/pending", headers=headers).json()
    assert len(pending) == 0
'''

with open('tests/test_received_invoices.py', 'a', encoding='utf-8') as f:
    f.write('\n\n' + new_test)

print('Test agregado exitosamente')
