with open('tests/test_company.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('def test_user_can_access_only_own_company_data(client):')
end = content.find('\ndef test_invoice_number_unique_per_company_not_global', start)

if start == -1 or end == -1:
    print("No se encontró el test")
else:
    new_test = '''def test_user_can_access_only_own_company_data(client):
    """Un usuario autenticado no puede acceder a datos de otra empresa (criterio #1 historia #46)."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Crear empresa A con usuario A
    company_a = client.post(
        "/companies",
        json={"name": "Empresa A", "tax_id": "B00000001", "address": "", "fiscal_year": "2026"},
        headers=headers,
    )
    assert company_a.status_code == 201
    company_a_id = company_a.json()["id"]

    # Crear empresa B con usuario A
    company_b = client.post(
        "/companies",
        json={"name": "Empresa B", "tax_id": "B00000002", "address": "", "fiscal_year": "2026"},
        headers=headers,
    )
    assert company_b.status_code == 201
    company_b_id = company_b.json()["id"]

    # Crear usuario B (obtiene membresía en empresa A, no en B)
    client.post(
        "/users",
        json={"email": "comprador@example.com", "password": "clave123"},
        headers=headers,
    )
    login_b = client.post(
        "/auth/login",
        json={"email": "comprador@example.com", "password": "clave123"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # Usuario B (miembro de empresa A) intenta acceder a empresa B (de la que NO es miembro)
    response = client.get("/company", headers={**headers_b, "X-Company-Id": str(company_b_id)})
    assert response.status_code == 403

    # Usuario B intenta listar asientos de empresa A (de la que NO es miembro)
    response = client.get("/journal-entries", headers={**headers_b, "X-Company-Id": str(company_a_id)})
    assert response.status_code == 403

'''

content = content[:start] + new_test + content[end:]

with open('tests/test_company.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Test updated successfully')
