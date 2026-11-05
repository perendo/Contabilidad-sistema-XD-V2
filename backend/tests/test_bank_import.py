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


def _bank_file(movements, iban=IBAN):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "movimientos"
    sheet["C3"] = "DIOCESIS DE GETAFE"
    sheet["B5"] = "Cuenta"
    if iban:
        sheet["C6"] = iban
    sheet["A7"] = "Fecha Operación"
    sheet["B7"] = "Fecha Valor"
    sheet["C7"] = "Concepto"
    sheet["D7"] = "Importe"
    for row, (operation_date, concept, amount) in enumerate(movements, start=8):
        sheet.cell(row=row, column=1, value=operation_date)
        sheet.cell(row=row, column=2, value=operation_date)
        sheet.cell(row=row, column=3, value=concept)
        sheet.cell(row=row, column=4, value=amount)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_import_creates_one_draft_per_movement_with_bank_and_555(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    pending = _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file(
                    [
                        ("27/02/2026", "Traspaso", "-595.0"),
                        ("26/02/2026", "Transferencia recibida", "100.0"),
                    ]
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
    assert {entry["status"] for entry in entries} == {"draft"}

    by_description = {entry["description"]: entry for entry in entries}

    outgoing = by_description["Traspaso"]
    assert outgoing["date"] == "2026-02-27"
    outgoing_lines = {line["account_id"]: line for line in outgoing["lines"]}
    assert outgoing_lines[bank["id"]]["credit"] == "595.00"
    assert outgoing_lines[bank["id"]]["debit"] == "0.00"
    assert outgoing_lines[pending["id"]]["debit"] == "595.00"
    assert outgoing_lines[pending["id"]]["credit"] == "0.00"

    incoming = by_description["Transferencia recibida"]
    assert incoming["date"] == "2026-02-26"
    incoming_lines = {line["account_id"]: line for line in incoming["lines"]}
    assert incoming_lines[bank["id"]]["debit"] == "100.00"
    assert incoming_lines[bank["id"]]["credit"] == "0.00"
    assert incoming_lines[pending["id"]]["credit"] == "100.00"
    assert incoming_lines[pending["id"]]["debit"] == "0.00"


def test_import_requires_account_for_new_iban(client):
    headers = _auth_headers(client)
    _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file([("27/02/2026", "Traspaso", "-595.0")]),
                XLSX_MIME,
            )
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "ES7400750248610600326588" in response.json()["detail"]
    assert client.get("/journal-entries", headers=headers).json() == []


def test_import_reuses_saved_iban_account(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    first = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file([("27/02/2026", "Primer movimiento", "-595.0")]),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file([("26/02/2026", "Segundo movimiento", "100.0")]),
                XLSX_MIME,
            )
        },
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json()["created"] == 1

    entries = client.get("/journal-entries", headers=headers).json()
    assert len(entries) == 2

    reused = next(entry for entry in entries if entry["description"] == "Segundo movimiento")
    lines = {line["account_id"]: line for line in reused["lines"]}
    assert lines[bank["id"]]["debit"] == "100.00"
    assert lines[bank["id"]]["credit"] == "0.00"


def test_import_with_invalid_rows_creates_nothing_and_reports_rows(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file(
                    [
                        ("27/02/2026", "Válido", "10.0"),
                        ("31/02/2026", "Fecha mala", "20.0"),
                        ("28/02/2026", "Importe malo", "no-es-numero"),
                    ]
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "9" in detail
    assert "fecha" in detail.lower()
    assert "10" in detail
    assert "importe" in detail.lower()
    assert client.get("/journal-entries", headers=headers).json() == []


def test_import_rejects_file_without_iban(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.xlsx",
                _bank_file(
                    [("27/02/2026", "Movimiento", "10.0")], iban=None
                ),
                XLSX_MIME,
            )
        },
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    assert "IBAN" in response.json()["detail"]
    assert client.get("/journal-entries", headers=headers).json() == []


def test_import_rejects_account_that_is_not_a_detail_bank_subaccount(client):
    headers = _auth_headers(client)
    group = _create_account(client, headers, "5720", "Bancos", is_detail=False)
    other = _create_account(client, headers, "7000", "Ventas", account_type="Ingreso")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    for account in (group, other):
        response = client.post(
            "/bank-imports",
            files={
                "file": (
                    "movimientos.xlsx",
                    _bank_file([("27/02/2026", "Movimiento", "10.0")]),
                    XLSX_MIME,
                )
            },
            data={"account_id": str(account["id"])},
            headers=headers,
        )

        assert response.status_code == 400
        assert account["code"] in response.json()["detail"]

    assert client.get("/journal-entries", headers=headers).json() == []





