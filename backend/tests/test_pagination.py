import pytest

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

LIST_URLS = [
    "/journal-entries",
    "/invoices",
    "/received-invoices",
    "/received-invoices/pending",
    "/users",
]


def _login(client):
    login = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return login.json()["access_token"]


@pytest.mark.parametrize("url", LIST_URLS)
@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 201}, {"offset": -1}],
)
def test_list_pagination_rejects_invalid_limit_and_offset(client, url, params):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    response = client.get(url, params=params, headers=headers)

    assert response.status_code == 422
