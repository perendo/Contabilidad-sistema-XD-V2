from io import BytesIO

from openpyxl import Workbook

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
IBAN = "ES74 0075 0248 61 0600326588"


def _auth_headers(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_account(client, headers, code, name, account_type="Activo", is_detail=True):
    response = client.post(
        "/accounts",
        json={
            "code": code,
            "name": name,
            "type": account_type,
            "level": 1,
            "is_detail": is_detail,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def _bank_file_custom(movements, col_date, col_concept, col_amount, iban=IBAN):
    workbook = Workbook()
    sheet = workbook.active
    sheet["C3"] = "DIOCESIS DE GETAFE"
    sheet["B5"] = "Cuenta"
    if iban:
        sheet["C6"] = iban
    sheet.cell(row=7, column=1, value=col_date)
    sheet.cell(row=7, column=2, value=col_concept)
    sheet.cell(row=7, column=3, value=col_amount)
    for row, (operation_date, concept, amount) in enumerate(movements, start=8):
        sheet.cell(row=row, column=1, value=operation_date)
        sheet.cell(row=row, column=2, value=concept)
        sheet.cell(row=row, column=3, value=amount)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_profile_applied_automatically_when_iban_has_profile(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    pending = _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    # save profile with custom columns
    profile_resp = client.post(
        "/bank-import-profiles",
        json={
            "iban": IBAN,
            "date_column": "FechaOp",
            "concept_column": "Detalle",
            "amount_column": "Valor",
        },
        headers=headers,
    )
    assert profile_resp.status_code == 201

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file_custom(
                    [
                        ("27/02/2026", "Traspaso", "-595.0"),
                        ("26/02/2026", "Transferencia recibida", "100.0"),
                    ],
                    "FechaOp",
                    "Detalle",
                    "Valor",
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["created"] == 2
    assert response.json()["iban"] == "ES7400750248610600326588"

    entries = client.get("/journal-entries", headers=headers).json()
    assert len(entries) == 2

    by_description = {entry["description"]: entry for entry in entries}
    outgoing = by_description["Traspaso"]
    outgoing_lines = {line["account_id"]: line for line in outgoing["lines"]}
    assert outgoing_lines[bank["id"]]["credit"] == "595.00"
    assert outgoing_lines[pending["id"]]["debit"] == "595.00"

    incoming = by_description["Transferencia recibida"]
    incoming_lines = {line["account_id"]: line for line in incoming["lines"]}
    assert incoming_lines[bank["id"]]["debit"] == "100.00"
    assert incoming_lines[pending["id"]]["credit"] == "100.00"


def test_profile_saved_when_mapping_provided_on_import(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    pending = _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    first = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file_custom(
                    [("27/02/2026", "Traspaso", "-595.0")],
                    "FechaOp",
                    "Detalle",
                    "Valor",
                ),
                XLSX_MIME,
            )
        },
        data={
            "account_id": str(bank["id"]),
            "date_column": "FechaOp",
            "concept_column": "Detalle",
            "amount_column": "Valor",
        },
        headers=headers,
    )
    assert first.status_code == 201
    assert first.json()["created"] == 1

    second = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file_custom(
                    [("26/02/2026", "Transferencia recibida", "100.0")],
                    "FechaOp",
                    "Detalle",
                    "Valor",
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json()["created"] == 1

    entries = client.get("/journal-entries", headers=headers).json()
    assert len(entries) == 2


def test_default_aliases_used_when_no_profile(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file_custom(
                    [("27/02/2026", "Traspaso", "-595.0")],
                    "Fecha Operación",
                    "Concepto",
                    "Importe",
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["created"] == 1


def test_import_requires_mapping_returns_headers_when_no_profile(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file_custom(
                    [("27/02/2026", "Traspaso", "-595.0")],
                    "FechaOp",
                    "Detalle",
                    "Valor",
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert isinstance(detail, dict)
    assert "headers" in detail
    assert "FechaOp" in detail["headers"]
    assert "Detalle" in detail["headers"]
    assert "Valor" in detail["headers"]
    assert client.get("/journal-entries", headers=headers).json() == []


IBAN2 = "ES12 3456 7890 1234 5678 9012"


def test_profile_not_reused_for_different_iban(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    # save profile for IBAN (original)
    client.post(
        "/bank-import-profiles",
        json={
            "iban": IBAN,
            "date_column": "FechaOp",
            "concept_column": "Detalle",
            "amount_column": "Valor",
        },
        headers=headers,
    )

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file_custom(
                    [("27/02/2026", "Traspaso", "-595.0")],
                    "FechaOp",
                    "Detalle",
                    "Valor",
                    iban=IBAN2,
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert isinstance(detail, dict)
    assert "headers" in detail