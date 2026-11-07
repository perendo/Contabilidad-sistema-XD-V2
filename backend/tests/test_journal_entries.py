TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import JournalEntry

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=create_engine(settings.test_database_url, pool_pre_ping=True)
)


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


def test_create_balanced_multi_line_entry_returns_201(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc_debit = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()
    acc_credit = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    payload = {
        "date": "2026-01-15",
        "description": "Venta de servicios",
        "lines": [
            {"account_id": acc_debit["id"], "description": "Cobro", "debit": 100, "credit": 0},
            {"account_id": acc_credit["id"], "description": "Ingreso", "debit": 0, "credit": 100},
        ],
    }
    post = client.post("/journal-entries", json=payload, headers=headers)
    assert post.status_code == 201
    data = post.json()
    assert data["date"] == "2026-01-15"
    assert data["description"] == "Venta de servicios"
    assert len(data["lines"]) == 2
    assert data["lines"][0]["debit"] == "100.00"
    assert data["lines"][1]["credit"] == "100.00"


def test_create_unbalanced_entry_returns_400_and_persists_nothing(client):
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

    payload = {
        "date": "2026-01-15",
        "description": "Asiento descuadrado",
        "lines": [
            {"account_id": acc_a["id"], "description": "Debe", "debit": 100, "credit": 0},
            {"account_id": acc_b["id"], "description": "Haber", "debit": 0, "credit": 90},
        ],
    }
    post = client.post("/journal-entries", json=payload, headers=headers)
    assert post.status_code == 400

    listing = client.get("/journal-entries", headers=headers)
    assert listing.status_code == 200
    assert listing.json() == []


def test_create_entry_with_invalid_account_or_amount_returns_400(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    acc = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True, "is_detail": True},
        headers=headers,
    ).json()

    # cuenta inexistente
    payload_bad_account = {
        "date": "2026-01-15",
        "description": "Cuenta inexistente",
        "lines": [
            {"account_id": 999999, "description": "Debe", "debit": 100, "credit": 0},
            {"account_id": acc["id"], "description": "Haber", "debit": 0, "credit": 100},
        ],
    }
    assert client.post("/journal-entries", json=payload_bad_account, headers=headers).status_code == 400

    # importe negativo
    payload_bad_amount = {
        "date": "2026-01-15",
        "description": "Importe negativo",
        "lines": [
            {"account_id": acc["id"], "description": "Debe", "debit": -5, "credit": 0},
            {"account_id": acc["id"], "description": "Haber", "debit": 0, "credit": -5},
        ],
    }
    assert client.post("/journal-entries", json=payload_bad_amount, headers=headers).status_code == 400


def test_list_entries_filters_by_date_range(client):
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

    for d in ("2026-01-10", "2026-01-20", "2026-02-05"):
        client.post(
            "/journal-entries",
            json={
                "date": d,
                "description": f"Entry {d}",
                "lines": [
                    {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                    {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
                ],
            },
            headers=headers,
        )

    filtered = client.get(
        "/journal-entries?date_from=2026-01-15&date_to=2026-01-31", headers=headers
    )
    assert filtered.status_code == 200
    dates = [e["date"] for e in filtered.json()]
    assert dates == ["2026-01-20"]


def test_update_draft_entry_persists_changes(client):
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

    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Borrador original",
            "status": "draft",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 100, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 100},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]

    updated = client.put(
        f"/journal-entries/{entry_id}",
        json={
            "date": "2026-01-16",
            "description": "Borrador editado",
            "lines": [
                {"account_id": acc_a["id"], "description": "D2", "debit": 50, "credit": 0},
                {"account_id": acc_b["id"], "description": "H2", "debit": 0, "credit": 50},
            ],
        },
        headers=headers,
    )
    assert updated.status_code == 200
    data = updated.json()
    assert data["date"] == "2026-01-16"
    assert data["description"] == "Borrador editado"
    assert data["status"] == "draft"
    assert len(data["lines"]) == 2
    assert data["lines"][0]["debit"] == "50.00"


def test_annul_draft_entry_keeps_it_in_journal(client):
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

    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Borrador a anular",
            "status": "draft",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]

    annulled = client.post(f"/journal-entries/{entry_id}/annul", headers=headers)
    assert annulled.status_code == 200
    assert annulled.json()["status"] == "annulled"

    listing = client.get("/journal-entries", headers=headers)
    assert listing.status_code == 200
    ids = [e["id"] for e in listing.json()]
    assert entry_id in ids
    match = [e for e in listing.json() if e["id"] == entry_id][0]
    assert match["status"] == "annulled"


def test_update_non_draft_entry_returns_400(client):
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

    # aceptado por defecto
    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Aceptado",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]

    updated = client.put(
        f"/journal-entries/{entry_id}",
        json={
            "date": "2026-01-16",
            "description": "Intento edición",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 5, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 5},
            ],
        },
        headers=headers,
    )
    assert updated.status_code == 400


def test_review_non_draft_entry_returns_400(client):
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

    line_payload = [
        {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
        {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
    ]

    accepted = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Aceptado", "lines": line_payload},
        headers=headers,
    ).json()
    assert client.post(f"/journal-entries/{accepted['id']}/review", headers=headers).status_code == 400

    draft = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Borrador", "status": "draft", "lines": line_payload},
        headers=headers,
    ).json()
    client.post(f"/journal-entries/{draft['id']}/annul", headers=headers)
    assert client.post(f"/journal-entries/{draft['id']}/review", headers=headers).status_code == 400


def test_accept_reviewed_balanced_draft_sets_accepted(client):
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

    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Borrador aceptable",
            "status": "draft",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]
    client.post(f"/journal-entries/{entry_id}/review", headers=headers)

    accepted = client.post(f"/journal-entries/{entry_id}/accept", headers=headers)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["reviewed"] is True


def test_accept_unreviewed_draft_returns_400(client):
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

    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Borrador no revisado",
            "status": "draft",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]

    response = client.post(f"/journal-entries/{entry_id}/accept", headers=headers)
    assert response.status_code == 400
    listing = client.get("/journal-entries", headers=headers).json()
    match = [e for e in listing if e["id"] == entry_id][0]
    assert match["status"] == "draft"


def test_accept_non_draft_entry_returns_400(client):
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

    line_payload = [
        {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
        {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
    ]

    accepted = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Aceptado", "lines": line_payload},
        headers=headers,
    ).json()
    assert client.post(f"/journal-entries/{accepted['id']}/accept", headers=headers).status_code == 400

    draft = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Borrador", "status": "draft", "lines": line_payload},
        headers=headers,
    ).json()
    client.post(f"/journal-entries/{draft['id']}/annul", headers=headers)
    assert client.post(f"/journal-entries/{draft['id']}/accept", headers=headers).status_code == 400


def test_correct_accepted_entry_creates_linked_accepted_entry(client):
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

    original = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento original",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    original_id = original["id"]
    assert original["status"] == "accepted"

    correction = client.post(
        f"/journal-entries/{original_id}/correct",
        json={
            "date": "2026-01-16",
            "description": "Corrección",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 5, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 5},
            ],
        },
        headers=headers,
    )
    assert correction.status_code == 201
    data = correction.json()
    assert data["status"] == "accepted"
    assert data["correction_of_entry_id"] == original_id
    assert data["corrects_entry_id"] == original_id
    assert data["original_entry_id"] == original_id

    # original unchanged
    orig_after = client.get("/journal-entries", headers=headers).json()
    match = [e for e in orig_after if e["id"] == original_id][0]
    assert match["status"] == "accepted"
    assert match["description"] == "Asiento original"


def test_correct_non_accepted_entry_returns_400(client):
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

    line_payload = [
        {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
        {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
    ]

    # borrador
    draft = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Borrador", "status": "draft", "lines": line_payload},
        headers=headers,
    ).json()
    assert client.post(
        f"/journal-entries/{draft['id']}/correct",
        json={"date": "2026-01-16", "description": "Corrección", "lines": line_payload},
        headers=headers,
    ).status_code == 400

    # anulado
    annulled = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "A anular", "status": "draft", "lines": line_payload},
        headers=headers,
    ).json()
    client.post(f"/journal-entries/{annulled['id']}/annul", headers=headers)
    assert client.post(
        f"/journal-entries/{annulled['id']}/correct",
        json={"date": "2026-01-16", "description": "Corrección", "lines": line_payload},
        headers=headers,
    ).status_code == 400


def test_correct_with_unbalanced_lines_returns_400(client):
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

    original = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Original",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()

    before = client.get("/journal-entries", headers=headers).json()
    before_ids = {e["id"] for e in before}

    response = client.post(
        f"/journal-entries/{original['id']}/correct",
        json={
            "date": "2026-01-16",
            "description": "Corrección mala",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 5},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 400

    after = client.get("/journal-entries", headers=headers).json()
    after_ids = {e["id"] for e in after}
    assert after_ids == before_ids


def test_delete_draft_entry_removes_it(client):
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

    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Borrador a borrar",
            "status": "draft",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]

    response = client.delete(f"/journal-entries/{entry_id}", headers=headers)
    assert response.status_code == 204

    listing = client.get("/journal-entries", headers=headers).json()
    assert entry_id not in {e["id"] for e in listing}


def test_delete_non_draft_entry_returns_400(client):
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

    line_payload = [
        {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
        {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
    ]

    # aceptado
    accepted = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Aceptado", "lines": line_payload},
        headers=headers,
    ).json()
    assert client.delete(f"/journal-entries/{accepted['id']}", headers=headers).status_code == 400

    # anulado
    draft = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Borrador", "status": "draft", "lines": line_payload},
        headers=headers,
    ).json()
    client.post(f"/journal-entries/{draft['id']}/annul", headers=headers)
    assert client.delete(f"/journal-entries/{draft['id']}", headers=headers).status_code == 400


def test_delete_nonexistent_entry_returns_404(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.delete("/journal-entries/999999", headers=headers).status_code == 404


def test_review_draft_entry_sets_reviewed_flag(client):
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

    created = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Borrador a revisar",
            "status": "draft",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    ).json()
    entry_id = created["id"]
    assert created.get("reviewed") is False

    reviewed = client.post(f"/journal-entries/{entry_id}/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["reviewed"] is True
    assert reviewed.json()["status"] == "draft"


def test_annul_non_draft_entry_returns_400(client):
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

    line_payload = [
        {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
        {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
    ]

    # aceptado
    accepted = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Aceptado", "lines": line_payload},
        headers=headers,
    ).json()
    assert client.post(f"/journal-entries/{accepted['id']}/annul", headers=headers).status_code == 400

    # ya anulado
    draft = client.post(
        "/journal-entries",
        json={"date": "2026-01-15", "description": "Borrador", "status": "draft", "lines": line_payload},
        headers=headers,
    ).json()
    client.post(f"/journal-entries/{draft['id']}/annul", headers=headers)
    assert client.post(f"/journal-entries/{draft['id']}/annul", headers=headers).status_code == 400


def test_manual_entry_records_its_creator_as_author(client):
    seed_headers = {"Authorization": f"Bearer {_login(client)}"}
    client.post(
        "/users",
        json={"email": "autor@example.com", "password": "clave123"},
        headers=seed_headers,
    )
    author_token = client.post(
        "/auth/login",
        json={"email": "autor@example.com", "password": "clave123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {author_token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True},
        headers=headers,
    ).json()

    response = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento con autor",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["author"] == "autor@example.com"


def test_entries_created_before_the_change_are_listed_without_author(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    try:
        legacy = JournalEntry(
            date=date(2026, 1, 10),
            description="Asiento anterior",
            status="accepted",
            company_id=1,
        )
        db.add(legacy)
        db.commit()
        legacy_id = legacy.id
    finally:
        db.close()

    listing = client.get("/journal-entries", headers=headers)
    assert listing.status_code == 200
    entry = next(e for e in listing.json() if e["id"] == legacy_id)
    assert entry["author"] is None


def test_correction_entry_records_the_author(client):
    seed_headers = {"Authorization": f"Bearer {_login(client)}"}
    client.post(
        "/users",
        json={"email": "corrector@example.com", "password": "clave123"},
        headers=seed_headers,
    )
    author_token = client.post(
        "/auth/login",
        json={"email": "corrector@example.com", "password": "clave123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {author_token}"}

    acc_a = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=seed_headers,
    ).json()
    acc_b = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True},
        headers=seed_headers,
    ).json()

    original = client.post(
        "/journal-entries",
        json={
            "date": "2026-01-15",
            "description": "Asiento original",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=seed_headers,
    ).json()

    correction = client.post(
        f"/journal-entries/{original['id']}/correct",
        json={
            "date": "2026-01-16",
            "description": "Corrección",
            "lines": [
                {"account_id": acc_a["id"], "description": "D", "debit": 10, "credit": 0},
                {"account_id": acc_b["id"], "description": "H", "debit": 0, "credit": 10},
            ],
        },
        headers=headers,
    )

    assert correction.status_code == 201
    assert correction.json()["author"] == "corrector@example.com"


def test_journal_entries_list_uses_constant_queries(client, count_queries):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    acc_debit = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    acc_credit = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True},
        headers=headers,
    ).json()

    def create_entry(day):
        return client.post(
            "/journal-entries",
            json={
                "date": f"2026-03-{day:02d}",
                "description": f"Asiento {day}",
                "lines": [
                    {"account_id": acc_debit["id"], "description": "D", "debit": 10, "credit": 0},
                    {"account_id": acc_credit["id"], "description": "H", "debit": 0, "credit": 10},
                ],
            },
            headers=headers,
        )

    assert create_entry(10).status_code == 201

    def measure():
        with count_queries() as statements:
            response = client.get("/journal-entries", headers=headers)
        assert response.status_code == 200
        return response, statements

    _, small = measure()

    for day in range(11, 15):
        assert create_entry(day).status_code == 201

    response, large = measure()

    assert len(large) == len(small)
    assert len(response.json()) == 5


def test_list_entries_paginates_with_limit_and_offset(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    acc_debit = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    acc_credit = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True},
        headers=headers,
    ).json()

    entry_ids = []
    for day in (10, 11, 12):
        created = client.post(
            "/journal-entries",
            json={
                "date": f"2026-04-{day:02d}",
                "description": f"Asiento {day}",
                "lines": [
                    {"account_id": acc_debit["id"], "description": "D", "debit": 10, "credit": 0},
                    {"account_id": acc_credit["id"], "description": "H", "debit": 0, "credit": 10},
                ],
            },
            headers=headers,
        ).json()
        entry_ids.append(created["id"])

    first_page = client.get(
        "/journal-entries", params={"limit": 2, "offset": 0}, headers=headers
    ).json()
    second_page = client.get(
        "/journal-entries", params={"limit": 2, "offset": 2}, headers=headers
    ).json()

    assert [entry["id"] for entry in first_page] == entry_ids[:2]
    assert [entry["id"] for entry in second_page] == entry_ids[2:]


def test_list_entries_uses_default_page_size(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    acc_debit = client.post(
        "/accounts",
        json={"code": "572", "name": "Bancos", "type": "Activo", "level": 1, "is_detail": True},
        headers=headers,
    ).json()
    acc_credit = client.post(
        "/accounts",
        json={"code": "700", "name": "Ventas", "type": "Ingreso", "level": 1, "is_detail": True},
        headers=headers,
    ).json()

    start = date(2026, 1, 1)
    for index in range(51):
        entry_date = (start + timedelta(days=index)).isoformat()
        created = client.post(
            "/journal-entries",
            json={
                "date": entry_date,
                "description": f"Asiento {index}",
                "lines": [
                    {"account_id": acc_debit["id"], "description": "D", "debit": 10, "credit": 0},
                    {"account_id": acc_credit["id"], "description": "H", "debit": 0, "credit": 10},
                ],
            },
            headers=headers,
        )
        assert created.status_code == 201

    default_page = client.get("/journal-entries", headers=headers).json()
    full_page = client.get(
        "/journal-entries", params={"limit": 200}, headers=headers
    ).json()

    assert len(default_page) == 50
    assert len(full_page) == 51