import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/companies",
        "/auth/login",
    ],
)
def test_cors_preflight_allows_x_company_id(client, path):
    """El preflight OPTIONS permite el encabezado X-Company-Id sin origen comodín."""
    response = client.options(
        path,
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Company-Id",
        },
    )
    assert response.status_code == 200
    allow_headers = response.headers.get("access-control-allow-headers", "")
    assert "x-company-id" in [h.strip().lower() for h in allow_headers.split(",")]
    assert response.headers.get("access-control-allow-origin") != "*"
    assert response.headers.get("access-control-allow-credentials") == "true"
