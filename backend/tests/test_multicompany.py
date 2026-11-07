TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _auth_headers(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_company(client, headers, name):
    resp = client.post("/companies", json={"name": name, "tax_id": "B00000000", "address": "", "fiscal_year": "2026"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def test_data_isolated_between_companies(client):
    headers = _auth_headers(client)

    company_a = _create_company(client, headers, "Empresa A")
    company_b = _create_company(client, headers, "Empresa B")

    # work in company A
    h_a = {**headers, "X-Company-Id": str(company_a["id"])}
    acc_a = client.post(
        "/accounts",
        json={"code": "100", "name": "Cuenta A", "type": "Activo", "level": 1, "is_detail": True},
        headers=h_a,
    )
    assert acc_a.status_code == 201

    # work in company B: account 100 should not exist
    h_b = {**headers, "X-Company-Id": str(company_b["id"])}
    list_b = client.get("/accounts", headers=h_b)
    assert list_b.status_code == 200
    assert all(a["code"] != "100" for a in list_b.json())

    # create 200 in B
    acc_b = client.post(
        "/accounts",
        json={"code": "200", "name": "Cuenta B", "type": "Activo", "level": 1, "is_detail": True},
        headers=h_b,
    )
    assert acc_b.status_code == 201

    # back to A: 200 should not exist
    list_a = client.get("/accounts", headers=h_a)
    assert all(a["code"] != "200" for a in list_a.json())
    assert any(a["code"] == "100" for a in list_a.json())


def test_new_company_starts_empty(client):
    headers = _auth_headers(client)
    company = _create_company(client, headers, "Empresa Nueva")
    h = {**headers, "X-Company-Id": str(company["id"])}

    accounts = client.get("/accounts", headers=h)
    assert accounts.status_code == 200
    assert accounts.json() == []

    entries = client.get("/journal-entries", headers=h)
    assert entries.status_code == 200
    assert entries.json() == []


def test_active_company_config_matches_selected(client):
    headers = _auth_headers(client)
    company_a = _create_company(client, headers, "Empresa A")
    company_b = _create_company(client, headers, "Empresa B")

    h_a = {**headers, "X-Company-Id": str(company_a["id"])}
    h_b = {**headers, "X-Company-Id": str(company_b["id"])}

    client.put("/company", json={"name": "Empresa A", "tax_id": "A111", "address": "Calle A", "fiscal_year": "2026"}, headers=h_a)
    client.put("/company", json={"name": "Empresa B", "tax_id": "B222", "address": "Calle B", "fiscal_year": "2026"}, headers=h_b)

    get_a = client.get("/company", headers=h_a)
    assert get_a.status_code == 200
    assert get_a.json()["name"] == "Empresa A"
    assert get_a.json()["tax_id"] == "A111"

    get_b = client.get("/company", headers=h_b)
    assert get_b.status_code == 200
    assert get_b.json()["name"] == "Empresa B"
    assert get_b.json()["tax_id"] == "B222"


def test_fiscal_endpoints_isolate_by_company(client):
    """SEC-CRIT-01: Los endpoints fiscales no deben devolver datos de otras empresas."""
    headers = _auth_headers(client)

    company_a = _create_company(client, headers, "Empresa A")
    company_b = _create_company(client, headers, "Empresa B")

    h_a = {**headers, "X-Company-Id": str(company_a["id"])}
    h_b = {**headers, "X-Company-Id": str(company_b["id"])}

    # Crear cuentas y terceros en empresa A
    acc_a = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto A", "type": "Gasto", "level": 1, "is_detail": True},
        headers=h_a,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA 21% A", "type": "Activo", "level": 1, "is_detail": True},
        headers=h_a,
    )
    third_a = client.post(
        "/third-parties",
        json={"name": "Proveedor A", "tax_id": "B11111111", "type": "proveedor", "account_id": acc_a["id"]},
        headers=h_a,
    ).json()

    # Crear factura en empresa A
    client.post(
        "/received-invoices",
        json={
            "date": "2026-01-15",
            "third_party_id": third_a["id"],
            "supplier_number": "F-A-001",
            "description": "Factura empresa A",
            "base_amount": 100.00,
            "vat_rate": 21,
            "expense_account_id": acc_a["id"],
        },
        headers=h_a,
    )

    # Crear cuenta y tercero en empresa B
    acc_b = client.post(
        "/accounts",
        json={"code": "6000", "name": "Gasto B", "type": "Gasto", "level": 1, "is_detail": True},
        headers=h_b,
    ).json()
    client.post(
        "/accounts",
        json={"code": "4720", "name": "IVA 21% B", "type": "Activo", "level": 1, "is_detail": True},
        headers=h_b,
    )
    third_b = client.post(
        "/third-parties",
        json={"name": "Proveedor B", "tax_id": "B22222222", "type": "proveedor", "account_id": acc_b["id"]},
        headers=h_b,
    ).json()

    # Crear factura en empresa B
    client.post(
        "/received-invoices",
        json={
            "date": "2026-01-15",
            "third_party_id": third_b["id"],
            "supplier_number": "F-B-001",
            "description": "Factura empresa B",
            "base_amount": 500.00,
            "vat_rate": 21,
            "expense_account_id": acc_b["id"],
        },
        headers=h_b,
    )

    # Empresa A no debe ver facturas de empresa B en IVA liquidation
    iva_a = client.get("/iva-liquidation", headers=h_a)
    assert iva_a.status_code == 200
    data_a = iva_a.json()
    assert data_a["iva_devengado"] == 0.0  # No hay facturas emitidas en A
    assert data_a["iva_deducible"] == 21.0  # Solo IVA de factura F-A-001 (100 * 21%)

    # Empresa B no debe ver facturas de empresa A en IVA liquidation
    iva_b = client.get("/iva-liquidation", headers=h_b)
    assert iva_b.status_code == 200
    data_b = iva_b.json()
    assert data_b["iva_devengado"] == 0.0
    assert data_b["iva_deducible"] == 105.0  # Solo IVA de factura F-B-001 (500 * 21%)

    # Libro registro: empresa A solo ve sus facturas
    libro_a = client.get("/libro-registro?year=2026", headers=h_a)
    assert libro_a.status_code == 200
    libro_a_data = libro_a.json()
    recibidas_a = [r for r in libro_a_data["recibidas"] if r["supplier_number"] == "F-A-001"]
    recibidas_b = [r for r in libro_a_data["recibidas"] if r["supplier_number"] == "F-B-001"]
    assert len(recibidas_a) == 1
    assert len(recibidas_b) == 0

    # Modelo 347: empresa A solo ve sus terceros
    m347_a = client.get("/modelo-347?year=2026&threshold=0", headers=h_a)
    assert m347_a.status_code == 200
    m347_a_data = m347_a.json()
    terceros_a = [t for t in m347_a_data["third_parties"] if t["tax_id"] == "B11111111"]
    terceros_b = [t for t in m347_a_data["third_parties"] if t["tax_id"] == "B22222222"]
    assert len(terceros_a) == 1
    assert len(terceros_b) == 0