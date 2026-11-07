TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def test_create_company_data_persists_and_returns(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
    }
    put = client.put("/company", json=payload, headers=headers)
    assert put.status_code in (200, 201)

    get = client.get("/company", headers=headers)
    assert get.status_code == 200
    data = get.json()
    assert data["name"] == payload["name"]
    assert data["tax_id"] == payload["tax_id"]
    assert data["address"] == payload["address"]
    assert data["fiscal_year"] == payload["fiscal_year"]

    # PGC base should be seeded automatically
    accs = client.get("/accounts", headers=headers)
    assert accs.status_code == 200
    assert len(accs.json()) >= 20

    suspense = next(a for a in accs.json() if a["code"] == "555")
    assert suspense["name"] == "Partidas pendientes de aplicación"
    assert suspense["type"] == "Activo"
    assert suspense["is_detail"] is True


def test_company_save_approval_threshold_returns_it(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "5000.00",
    }
    put = client.put("/company", json=payload, headers=headers)
    assert put.status_code == 200
    assert put.json()["approval_threshold"] == "5000.00"

    get = client.get("/company", headers=headers)
    assert get.status_code == 200
    assert get.json()["approval_threshold"] == "5000.00"


def test_company_rejects_invalid_approval_threshold(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
        "approval_threshold": "0",
    }
    put = client.put("/company", json=payload, headers=headers)
    assert put.status_code == 400

    get = client.get("/company", headers=headers)
    assert get.status_code == 200
    assert get.json()["approval_threshold"] is None


def test_update_company_does_not_reseed_pgc_when_accounts_exist(client, monkeypatch):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Empresa SL",
        "tax_id": "B12345678",
        "address": "Calle Principal 1",
        "fiscal_year": "2026",
    }
    first = client.put("/company", json=payload, headers=headers)
    assert first.status_code == 200

    calls = []

    def fake_seed(db):
        calls.append(True)
        return 0

    monkeypatch.setattr("app.company.seed_pgc", fake_seed)

    payload["name"] = "Empresa Actualizada SL"
    second = client.put("/company", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["name"] == payload["name"]
    assert calls == []


def test_company_rejects_tenant_spoofing_403(client):
    """Un usuario autenticado no puede acceder a una empresa de la que no es miembro (BOLA/IDOR)."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # El usuario test crea una segunda empresa (obtiene membresía en ella)
    company_b = client.post(
        "/companies",
        json={
            "name": "Empresa B",
            "tax_id": "B00000001",
            "address": "",
            "fiscal_year": "2026",
        },
        headers=headers,
    )
    assert company_b.status_code == 201
    company_b_id = company_b.json()["id"]

    # Crear un segundo usuario (obtendrá membresía en la empresa 1, no en la B)
    client.post(
        "/users",
        json={"email": "atacante@example.com", "password": "clave456"},
        headers=headers,
    )
    atacante_token = client.post(
        "/auth/login",
        json={"email": "atacante@example.com", "password": "clave456"},
    ).json()["access_token"]
    atacante_headers = {"Authorization": f"Bearer {atacante_token}"}

    # El atacante intenta acceder a la empresa B (de la que NO es miembro)
    headers_b = {**atacante_headers, "X-Company-Id": str(company_b_id)}
    response = client.get("/company", headers=headers_b)
    assert response.status_code == 403

    # También falla al intentar listar cuentas de la empresa B
    response = client.get("/accounts", headers=headers_b)
    assert response.status_code == 403

    # El atacante solo puede acceder a su propia empresa (la 1)
    response = client.get("/company", headers=atacante_headers)
    assert response.status_code == 200

def test_invoice_number_unique_per_company_not_global(client):
    """Dos empresas distintas pueden emitir facturas con el mismo número y año."""
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Crear dos empresas
    company_a = client.post(
        "/companies",
        json={"name": "Empresa A", "tax_id": "B00000001", "address": "", "fiscal_year": "2026"},
        headers=headers,
    ).json()
    company_b = client.post(
        "/companies",
        json={"name": "Empresa B", "tax_id": "B00000002", "address": "", "fiscal_year": "2026"},
        headers=headers,
    ).json()

    # Crear terceros y cuentas necesarias para cada empresa
    # Empresa A: cuenta gasto y tercero
    acc_a = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto A", "type": "Gasto", "level": 1, "is_detail": True},
        headers={**headers, "X-Company-Id": str(company_a["id"])},
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA 21% A", "type": "Activo", "level": 1, "is_detail": True},
        headers={**headers, "X-Company-Id": str(company_a["id"])},
    )
    third_a = client.post(
        "/third-parties",
        json={"name": "Proveedor A", "tax_id": "B11111111", "type": "proveedor", "account_id": acc_a["id"]},
        headers={**headers, "X-Company-Id": str(company_a["id"])},
    ).json()

    # Empresa B: cuenta gasto y tercero
    acc_b = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto B", "type": "Gasto", "level": 1, "is_detail": True},
        headers={**headers, "X-Company-Id": str(company_b["id"])},
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA 21% B", "type": "Activo", "level": 1, "is_detail": True},
        headers={**headers, "X-Company-Id": str(company_b["id"])},
    )
    third_b = client.post(
        "/third-parties",
        json={"name": "Proveedor B", "tax_id": "B22222222", "type": "proveedor", "account_id": acc_b["id"]},
        headers={**headers, "X-Company-Id": str(company_b["id"])},
    ).json()

    # Empresa A emite factura número 1 del año 2026
    inv_a = client.post(
        "/received-invoices",
        json={
            "date": "2026-01-15",
            "third_party_id": third_a["id"],
            "supplier_number": "F-001",
            "description": "Factura A",
            "base_amount": 100.00,
            "vat_rate": 21,
            "expense_account_id": acc_a["id"],
        },
        headers={**headers, "X-Company-Id": str(company_a["id"])},
    )
    assert inv_a.status_code == 201

    # Empresa B emite factura número 1 del mismo año 2026 (debe permitirlo)
    inv_b = client.post(
        "/received-invoices",
        json={
            "date": "2026-01-15",
            "third_party_id": third_b["id"],
            "supplier_number": "F-001",
            "description": "Factura B",
            "base_amount": 200.00,
            "vat_rate": 21,
            "expense_account_id": acc_b["id"],
        },
        headers={**headers, "X-Company-Id": str(company_b["id"])},
    )
    assert inv_b.status_code == 201

    # Empresa A no puede emitir factura número 1 del mismo año (debe fallar)
    inv_a_dup = client.post(
        "/received-invoices",
        json={
            "date": "2026-01-15",
            "third_party_id": third_a["id"],
            "supplier_number": "F-001",
            "description": "Factura A duplicada",
            "base_amount": 300.00,
            "vat_rate": 21,
            "expense_account_id": acc_a["id"],
        },
        headers={**headers, "X-Company-Id": str(company_a["id"])},
    )
    assert inv_a_dup.status_code == 409
