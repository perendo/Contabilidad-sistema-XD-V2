TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


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
