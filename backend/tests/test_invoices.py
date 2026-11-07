from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from fastapi.testclient import TestClient

from app.main import app

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def _setup_accounts_and_client(client, headers, include_default_accounts=True):
    accounts = {}
    codes = [("4300", "Clientes generales", "Activo")]
    if include_default_accounts:
        codes += [
            ("7000", "Ventas de mercaderías nacionales", "Ingreso"),
            ("4770", "Hacienda Pública, IVA repercutido 21%", "Pasivo"),
        ]
    for code, name, account_type in codes:
        accounts[code] = client.post(
            "/accounts",
            json={"code": code, "name": name, "type": account_type, "level": 1, "is_detail": True, "is_detail": True},
            headers=headers,
        ).json()
    client_third_party = client.post(
        "/third-parties",
        json={
            "name": "Cliente Uno SL",
            "tax_id": "B12345678",
            "type": "cliente",
            "account_id": accounts["4300"]["id"],
        },
        headers=headers,
    ).json()
    return accounts, client_third_party


def test_create_issued_invoice_returns_number_totals_and_lists_it(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    payload = {
        "date": "2026-03-10",
        "client_id": client_third_party["id"],
        "description": "Servicios de consultoría",
        "base_amount": 100,
        "vat_rate": 21,
    }
    post = client.post("/invoices", json=payload, headers=headers)
    assert post.status_code == 201
    data = post.json()
    assert data["year"] == 2026
    assert data["number"] == 1
    assert data["date"] == "2026-03-10"
    assert data["third_party_id"] == client_third_party["id"]
    assert data["description"] == "Servicios de consultoría"
    assert data["base_amount"] == 100
    assert data["vat_rate"] == 21
    assert data["vat_amount"] == 21
    assert data["total"] == 121

    listing = client.get("/invoices", headers=headers)
    assert listing.status_code == 200
    listed = listing.json()
    assert len(listed) == 1
    assert listed[0]["id"] == data["id"]
    assert listed[0]["base_amount"] == 100
    assert listed[0]["vat_amount"] == 21
    assert listed[0]["total"] == 121


def test_issued_invoice_number_is_sequential_per_fiscal_year(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    def create(date):
        return client.post(
            "/invoices",
            json={
                "date": date,
                "client_id": client_third_party["id"],
                "description": "Servicio",
                "base_amount": 50,
                "vat_rate": 21,
            },
            headers=headers,
        ).json()

    first_2026 = create("2026-01-05")
    second_2026 = create("2026-12-31")
    first_2027 = create("2027-01-02")

    assert (first_2026["year"], first_2026["number"]) == (2026, 1)
    assert (second_2026["year"], second_2026["number"]) == (2026, 2)
    assert (first_2027["year"], first_2027["number"]) == (2027, 1)


def test_journal_entry_description_shows_formatted_invoice_number(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    created = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": client_third_party["id"],
            "description": "Servicio",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    ).json()

    entries = client.get("/journal-entries", headers=headers).json()
    entry = next(e for e in entries if e["id"] == created["entry_id"])
    assert entry["description"].startswith("Factura 2026/0001")


def test_concurrent_invoices_receive_distinct_sequential_numbers(client):
    token = _login(client)
    company_id = client.cookies.get("active_company_id")
    headers = {"Authorization": f"Bearer {token}", "X-Company-Id": company_id}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    payload = {
        "date": "2026-06-15",
        "client_id": client_third_party["id"],
        "description": "Servicio",
        "base_amount": 100,
        "vat_rate": 21,
    }
    workers = 4
    barrier = Barrier(workers)

    def create_invoice():
        concurrent_client = TestClient(app)
        barrier.wait(timeout=10)
        try:
            return concurrent_client.post("/invoices", json=payload, headers=headers)
        finally:
            concurrent_client.close()

    for expected_numbers in (list(range(1, 5)), list(range(5, 9))):
        with ThreadPoolExecutor(max_workers=workers) as executor:
            responses = list(executor.map(lambda _: create_invoice(), range(workers)))

        assert [response.status_code for response in responses] == [201] * workers
        assert sorted(response.json()["number"] for response in responses) == expected_numbers


def test_issued_invoice_generates_balanced_accepted_journal_entry(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, client_third_party = _setup_accounts_and_client(client, headers)

    invoice = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": client_third_party["id"],
            "description": "Servicios de consultoría",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    ).json()
    assert invoice["entry_id"] is not None

    entries = client.get("/journal-entries", headers=headers).json()
    entry = [e for e in entries if e["id"] == invoice["entry_id"]][0]
    assert entry["status"] == "accepted"
    assert entry["date"] == "2026-03-10"

    lines = {(l["account_id"], l["debit"], l["credit"]) for l in entry["lines"]}
    assert lines == {
        (accounts["4300"]["id"], "121.00", "0.00"),
        (accounts["7000"]["id"], "0.00", "100.00"),
        (accounts["4770"]["id"], "0.00", "21.00"),
    }
    assert sum(Decimal(l["debit"]) for l in entry["lines"]) == sum(Decimal(l["credit"]) for l in entry["lines"])


def test_issued_invoice_with_unknown_or_supplier_client_returns_400_and_persists_nothing(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, _ = _setup_accounts_and_client(client, headers)
    supplier = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Dos SL",
            "tax_id": "B87654321",
            "type": "proveedor",
            "account_id": accounts["4770"]["id"],
        },
        headers=headers,
    ).json()

    payload = {
        "date": "2026-03-10",
        "description": "Servicio",
        "base_amount": 100,
        "vat_rate": 21,
    }

    unknown = client.post(
        "/invoices", json={**payload, "client_id": 999999}, headers=headers
    )
    assert unknown.status_code == 400

    supplier_client = client.post(
        "/invoices", json={**payload, "client_id": supplier["id"]}, headers=headers
    )
    assert supplier_client.status_code == 400

    assert client.get("/invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_issued_invoice_with_non_positive_base_or_invalid_vat_rate_returns_400(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    payload = {
        "date": "2026-03-10",
        "client_id": client_third_party["id"],
        "description": "Servicio",
        "base_amount": 100,
        "vat_rate": 21,
    }

    for base_amount in (0, -10):
        assert (
            client.post(
                "/invoices",
                json={**payload, "base_amount": base_amount},
                headers=headers,
            ).status_code
            == 400
        )

    for vat_rate in (7, 12):
        assert (
            client.post(
                "/invoices", json={**payload, "vat_rate": vat_rate}, headers=headers
            ).status_code
            == 400
        )

    assert client.get("/invoices", headers=headers).json() == []


def test_issued_invoice_with_missing_default_accounts_returns_400_and_persists_nothing(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(
        client, headers, include_default_accounts=False
    )

    post = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": client_third_party["id"],
            "description": "Servicio",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    )
    assert post.status_code == 400
    assert client.get("/invoices", headers=headers).json() == []
    assert client.get("/journal-entries", headers=headers).json() == []


def test_issued_invoice_with_description_over_500_chars_is_rejected(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    post = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": client_third_party["id"],
            "description": "x" * 501,
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    )
    assert post.status_code == 422
    assert client.get("/invoices", headers=headers).json() == []


def test_issued_invoice_with_out_of_range_base_or_extra_decimals_is_rejected(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _, client_third_party = _setup_accounts_and_client(client, headers)

    payload = {
        "date": "2026-03-10",
        "client_id": client_third_party["id"],
        "description": "Servicio",
        "vat_rate": 21,
    }
    # supera Numeric(12,2) de la base
    assert (
        client.post(
            "/invoices", json={**payload, "base_amount": 100000000000}, headers=headers
        ).status_code
        == 422
    )
    # más de dos decimales
    assert (
        client.post(
            "/invoices", json={**payload, "base_amount": 0.001}, headers=headers
        ).status_code
        == 422
    )
    assert client.get("/invoices", headers=headers).json() == []


def test_invoice_number_not_consumed_by_any_rejected_attempt(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    accounts, client_third_party = _setup_accounts_and_client(client, headers)
    supplier = client.post(
        "/third-parties",
        json={
            "name": "Proveedor Dos SL",
            "tax_id": "B87654321",
            "type": "proveedor",
            "account_id": accounts["4770"]["id"],
        },
        headers=headers,
    ).json()

    valid_payload = {
        "date": "2026-05-20",
        "client_id": client_third_party["id"],
        "description": "Servicio",
        "base_amount": 100,
        "vat_rate": 21,
    }
    first = client.post("/invoices", json=valid_payload, headers=headers).json()
    assert first["number"] == 1

    rejected_payloads = [
        {**valid_payload, "client_id": supplier["id"]},
        {**valid_payload, "base_amount": 0},
        {**valid_payload, "vat_rate": 7},
    ]
    for payload in rejected_payloads:
        assert client.post("/invoices", json=payload, headers=headers).status_code == 400

    second = client.post("/invoices", json=valid_payload, headers=headers).json()
    assert second["number"] == 2
    listed = client.get("/invoices", headers=headers).json()
    assert sorted(invoice["number"] for invoice in listed) == [1, 2]


def test_issued_invoice_and_its_collection_entry_record_the_author(client):
    seed_headers = {"Authorization": f"Bearer {_login(client)}"}
    client.post(
        "/users",
        json={"email": "facturador@example.com", "password": "clave123"},
        headers=seed_headers,
    )
    author_token = client.post(
        "/auth/login",
        json={"email": "facturador@example.com", "password": "clave123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {author_token}"}

    _, client_third_party = _setup_accounts_and_client(client, headers)
    client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    )

    invoice = client.post(
        "/invoices",
        json={
            "date": "2026-03-10",
            "client_id": client_third_party["id"],
            "description": "Servicio",
            "base_amount": 100,
            "vat_rate": 21,
        },
        headers=headers,
    ).json()

    entries = client.get("/journal-entries", headers=headers).json()
    invoice_entry = next(e for e in entries if e["id"] == invoice["entry_id"])
    assert invoice_entry["author"] == "facturador@example.com"

    paid = client.post(
        f"/invoices/{invoice['id']}/pay",
        json={"status": "cobrada"},
        headers=headers,
    )
    assert paid.status_code == 200

    entries = client.get("/journal-entries", headers=headers).json()
    collection_entry = next(e for e in entries if e["id"] != invoice["entry_id"])
    assert collection_entry["author"] == "facturador@example.com"
