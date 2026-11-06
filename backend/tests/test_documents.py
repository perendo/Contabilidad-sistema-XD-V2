from app.config import settings

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def _auth_headers(client):
    token = _login(client)
    return {"Authorization": f"Bearer {token}"}


def _create_account(client, headers, code, name, account_type):
    return client.post(
        "/accounts",
        json={
            "code": code,
            "name": name,
            "type": account_type,
            "level": 1,
            "is_detail": True,
        },
        headers=headers,
    ).json()


def _create_entry(client, headers, entry_date, status=None):
    account_a = _create_account(client, headers, "572", "Bancos", "Activo")
    account_b = _create_account(client, headers, "700", "Ventas", "Ingreso")
    payload = {
        "date": entry_date,
        "description": "Asiento con documento",
        "lines": [
            {"account_id": account_a["id"], "description": "D", "debit": 10, "credit": 0},
            {"account_id": account_b["id"], "description": "H", "debit": 0, "credit": 10},
        ],
    }
    if status is not None:
        payload["status"] = status
    entry = client.post("/journal-entries", json=payload, headers=headers).json()
    return entry, account_a, account_b


def _configure_company(client, headers, name="Acme SL"):
    response = client.put(
        "/company",
        json={
            "name": name,
            "tax_id": "B12345678",
            "address": "Calle Mayor 1",
            "fiscal_year": "2026",
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _stored_files():
    return [path for path in settings.documents_dir.rglob("*") if path.is_file()]


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def test_attach_document_to_entry_returns_201_with_metadata(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    response = client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/xml")},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["entry_id"] == entry_id
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/xml"
    assert data["size"] == len(b"hello world")
    assert "id" in data


def test_list_entry_documents_returns_attached_metadata(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("a.txt", b"aaa", "text/xml")},
        headers=headers,
    )
    client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("b.txt", b"bbbbb", "text/xml")},
        headers=headers,
    )

    response = client.get(f"/journal-entries/{entry_id}/attachments", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    names = {d["filename"] for d in data}
    assert names == {"a.txt", "b.txt"}
    for d in data:
        assert d["entry_id"] == entry_id
        assert "size" in d


def test_download_entry_document_returns_original_content(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    uploaded = client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("hello.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()
    doc_id = uploaded["id"]

    response = client.get(
        f"/attachments/{doc_id}", headers=headers
    )
    assert response.status_code == 200
    assert response.content == b"hello world"
    assert response.headers["content-type"].startswith("text/xml")
    assert "hello.txt" in response.headers.get("content-disposition", "")


def test_attach_document_to_unknown_entry_returns_404(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/journal-entries/999999/attachments",
        files={"file": ("test.txt", b"hello", "text/xml")},
        headers=headers,
    )
    assert response.status_code == 404


def test_list_documents_of_entry_without_attachments_returns_empty(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento sin documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    response = client.get(f"/journal-entries/{entry_id}/attachments", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_delete_scoped_document_removes_it(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    uploaded = client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()
    doc_id = uploaded["id"]

    response = client.delete(
        f"/attachments/{doc_id}", headers=headers
    )
    assert response.status_code == 204

    listing = client.get(f"/journal-entries/{entry_id}/attachments", headers=headers)
    assert listing.status_code == 200
    assert listing.json() == []

    download = client.get(
        f"/attachments/{doc_id}", headers=headers
    )
    assert download.status_code == 404


def test_delete_direct_document_by_id_removes_it(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    uploaded = client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()
    doc_id = uploaded["id"]

    response = client.delete(f"/attachments/{doc_id}", headers=headers)
    assert response.status_code == 204

    download = client.get(f"/attachments/{doc_id}", headers=headers)
    assert download.status_code == 404


def test_delete_unknown_document_returns_404(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/attachments/999999", headers=headers)
    assert response.status_code == 404

    download = client.get("/attachments/999999", headers=headers)
    assert download.status_code == 404


def test_legacy_document_alias_routes_are_not_exposed(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    for path in (
        "/documents/1",
        "/journal-entries/1/documents",
        "/entries/1/adjuntos",
        "/asientos/1/documentos",
    ):
        assert client.get(path, headers=headers).status_code == 404


def test_delete_document_twice_returns_404_on_second(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    entry = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con documento",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = entry["id"]

    uploaded = client.post(
        f"/journal-entries/{entry_id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()
    doc_id = uploaded["id"]

    first = client.delete(f"/attachments/{doc_id}", headers=headers)
    assert first.status_code == 204

    second = client.delete(f"/attachments/{doc_id}", headers=headers)
    assert second.status_code == 404


def test_upload_stores_document_in_company_and_entry_year_folder(client):
    headers = _auth_headers(client)
    entry, _, _ = _create_entry(client, headers, "2026-01-15")
    _configure_company(client, headers, name="Acme SL")

    response = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("factura.pdf", b"%PDF-1.4 demo", "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 201

    files = _stored_files()
    assert len(files) == 1
    stored = files[0]
    assert stored.parent.name == "2026"
    assert stored.parent.parent.name == "Acme SL"
    assert stored.suffix == ".pdf"
    assert stored.stem != "factura"
    assert stored.read_bytes() == b"%PDF-1.4 demo"


def test_company_name_is_sanitized_for_the_storage_folder(client):
    headers = _auth_headers(client)
    entry, _, _ = _create_entry(client, headers, "2026-01-15")
    _configure_company(client, headers, name="Acme/SL: 2026")

    client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("factura.pdf", b"%PDF-1.4 demo", "application/pdf")},
        headers=headers,
    )

    stored = _stored_files()[0]
    assert stored.parent.parent.name == "Acme_SL_ 2026"


def test_download_reads_document_from_disk(client):
    headers = _auth_headers(client)
    entry, _, _ = _create_entry(client, headers, "2026-01-15")
    _configure_company(client, headers)

    uploaded = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("hello.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()

    stored = _stored_files()[0]
    stored.write_bytes(b"contenido cambiado en disco")

    response = client.get(f"/attachments/{uploaded['id']}", headers=headers)
    assert response.status_code == 200
    assert response.content == b"contenido cambiado en disco"


def test_download_returns_404_when_file_is_missing(client):
    headers = _auth_headers(client)
    entry, _, _ = _create_entry(client, headers, "2026-01-15")
    _configure_company(client, headers)

    uploaded = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("hello.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()

    _stored_files()[0].unlink()

    response = client.get(f"/attachments/{uploaded['id']}", headers=headers)
    assert response.status_code == 404


def test_delete_attachment_removes_file_from_disk(client):
    headers = _auth_headers(client)
    entry, _, _ = _create_entry(client, headers, "2026-01-15")
    _configure_company(client, headers)

    uploaded = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("hello.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()

    stored = _stored_files()[0]
    assert stored.exists()

    response = client.delete(f"/attachments/{uploaded['id']}", headers=headers)
    assert response.status_code == 204
    assert not stored.exists()
    assert _stored_files() == []


def test_upload_stores_document_under_entry_company_folder(client):
    headers = _auth_headers(client)

    company_two = client.post(
        "/companies",
        json={"name": "Empresa Dos", "tax_id": "B222", "address": "Calle 2", "fiscal_year": "2026"},
        headers=headers,
    ).json()
    headers_two = {**headers, "X-Company-Id": str(company_two["id"])}

    # Create the entry before configuring the company so the needed accounts can be created.
    entry, _, _ = _create_entry(client, headers_two, "2026-01-15")

    client.put(
        "/company",
        json={"name": "Empresa Dos", "tax_id": "B222", "address": "Calle 2", "fiscal_year": "2026"},
        headers=headers_two,
    )

    response = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("factura.pdf", b"%PDF-1.4 demo", "application/pdf")},
        headers=headers_two,
    )
    assert response.status_code == 201

    files = _stored_files()
    assert len(files) == 1
    stored = files[0]
    assert stored.parent.parent.name == "Empresa Dos"


def test_document_access_is_scoped_to_entry_company(client):
    headers = _auth_headers(client)

    company_two = client.post(
        "/companies",
        json={"name": "Empresa Dos", "tax_id": "B222", "address": "Calle 2", "fiscal_year": "2026"},
        headers=headers,
    ).json()
    headers_two = {**headers, "X-Company-Id": str(company_two["id"])}

    entry, _, _ = _create_entry(client, headers, "2026-01-15")

    uploaded = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("hello.txt", b"hello world", "text/xml")},
        headers=headers,
    ).json()

    response = client.get(f"/attachments/{uploaded['id']}", headers=headers_two)
    assert response.status_code == 404


def test_changing_draft_entry_year_moves_documents(client):
    headers = _auth_headers(client)
    entry, account_a, account_b = _create_entry(
        client, headers, "2026-12-31", status="draft"
    )
    _configure_company(client, headers)

    uploaded = client.post(
        f"/journal-entries/{entry['id']}/attachments",
        files={"file": ("justificante.xml", b"<xml/>", "text/xml")},
        headers=headers,
    ).json()

    old_file = _stored_files()[0]
    assert old_file.parent.name == "2026"

    response = client.put(
        f"/journal-entries/{entry['id']}",
        json={
            "date": "2027-01-02",
            "description": "Asiento movido de ejercicio",
            "lines": [
                {"account_id": account_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": account_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200

    files = _stored_files()
    assert len(files) == 1
    new_file = files[0]
    assert new_file.parent.name == "2027"
    assert new_file.name == old_file.name
    assert not old_file.exists()

    download = client.get(f"/attachments/{uploaded['id']}", headers=headers)
    assert download.status_code == 200
    assert download.content == b"<xml/>"
