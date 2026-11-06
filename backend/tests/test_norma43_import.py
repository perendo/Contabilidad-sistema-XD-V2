from datetime import datetime
from io import BytesIO

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"
CSB_MIME = "text/plain"
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


def _csb_file(movements, iban=IBAN):
    iban_norm = iban.replace(" ", "").upper()
    lines = []
    header = list(" " * 100)
    header[0:2] = list("01")
    field = iban_norm.ljust(34)
    for i, ch in enumerate(field):
        header[26 + i] = ch
    lines.append("".join(header))
    for operation_date, concept, code, amount in movements:
        d = datetime.strptime(operation_date, "%d/%m/%Y").strftime("%Y%m%d")
        amt_str = f"{int(round(amount * 10000)):016d}"
        concept_field = concept.ljust(48)[:48]
        line = code + "    " + d + "        " + concept_field + amt_str + " " * 14
        assert len(line) == 100, len(line)
        lines.append(line)
    return "\n".join(lines).encode("latin-1")


def test_norma43_import_creates_one_draft_per_movement_with_bank_and_555(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    pending = _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.csb",
                _csb_file(
                    [
                        ("27/02/2026", "Traspaso", "21", 595.0),
                        ("26/02/2026", "Transferencia recibida", "22", 100.0),
                    ]
                ),
                CSB_MIME,
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


def test_norma43_import_reuses_saved_iban_account(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    first = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.csb",
                _csb_file([("27/02/2026", "Primer movimiento", "21", 595.0)]),
                CSB_MIME,
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
                "movimientos.csb",
                _csb_file([("26/02/2026", "Segundo movimiento", "22", 100.0)]),
                CSB_MIME,
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


def test_norma43_import_requires_account_for_new_iban(client):
    headers = _auth_headers(client)
    _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    response = client.post(
        "/bank-imports",
        files={
            "file": (
                "movimientos.csb",
                _csb_file([("27/02/2026", "Traspaso", "21", 595.0)]),
                CSB_MIME,
            )
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "ES7400750248610600326588" in response.json()["detail"]
    assert client.get("/journal-entries", headers=headers).json() == []


def test_norma43_import_with_invalid_rows_creates_nothing_and_reports_rows(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    iban_norm = IBAN.replace(" ", "").upper()
    header = list(" " * 100)
    header[0:2] = list("01")
    field = iban_norm.ljust(34)
    for i, ch in enumerate(field):
        header[26 + i] = ch
    lines = ["".join(header)]

    # valid row (line 2)
    valid = "22    " + "20260227" + "        " + "Valido".ljust(48) + f"{int(round(10.0 * 10000)):016d}" + " " * 14
    assert len(valid) == 100
    lines.append(valid)

    # invalid date (line 3)
    bad_date = "22    " + "99999999" + "        " + "Fecha mala".ljust(48) + f"{int(round(20.0 * 10000)):016d}" + " " * 14
    assert len(bad_date) == 100
    lines.append(bad_date)

    # invalid amount (line 4)
    bad_amount = "22    " + "20260228" + "        " + "Importe malo".ljust(48) + "ABCDEFGHIJKLMNPQ" + " " * 14
    assert len(bad_amount) == 100
    lines.append(bad_amount)

    content = "\n".join(lines).encode("latin-1")

    response = client.post(
        "/bank-imports",
        files={"file": ("movimientos.csb", content, CSB_MIME)},
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "3" in detail
    assert "fecha" in detail.lower()
    assert "4" in detail
    assert "importe" in detail.lower()
    assert client.get("/journal-entries", headers=headers).json() == []


def test_norma43_import_rejects_file_without_iban(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    # header without IBAN (spaces in field)
    header = "01" + " " * 98
    assert len(header) == 100
    movement = "22    " + "20260227" + "        " + "Movimiento".ljust(48) + f"{int(round(10.0 * 10000)):016d}" + " " * 14
    assert len(movement) == 100
    content = (header + "\n" + movement).encode("latin-1")

    response = client.post(
        "/bank-imports",
        files={"file": ("movimientos.csb", content, CSB_MIME)},
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    assert "IBAN" in response.json()["detail"]
    assert client.get("/journal-entries", headers=headers).json() == []


def test_norma43_import_rejects_account_that_is_not_a_detail_bank_subaccount(client):
    headers = _auth_headers(client)
    group = _create_account(client, headers, "5720", "Bancos", is_detail=False)
    other = _create_account(client, headers, "7000", "Ventas", account_type="Ingreso")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    for account in (group, other):
        response = client.post(
            "/bank-imports",
            files={
                "file": (
                    "movimientos.csb",
                    _csb_file([("27/02/2026", "Movimiento", "22", 10.0)]),
                    CSB_MIME,
                )
            },
            data={"account_id": str(account["id"])},
            headers=headers,
        )

        assert response.status_code == 400
        assert account["code"] in response.json()["detail"]

    assert client.get("/journal-entries", headers=headers).json() == []


def test_norma43_import_rejects_non_csb_text_file(client):
    headers = _auth_headers(client)
    bank = _create_account(client, headers, "5720001", "Banco principal")
    _create_account(client, headers, "555", "Partidas pendientes de aplicación")

    content = b"Esto no es un fichero Norma 43\nsolo texto libre\n"

    response = client.post(
        "/bank-imports",
        files={"file": ("notas.txt", content, CSB_MIME)},
        data={"account_id": str(bank["id"])},
        headers=headers,
    )

    assert response.status_code == 400
    assert client.get("/journal-entries", headers=headers).json() == []