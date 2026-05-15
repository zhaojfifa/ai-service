from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _configure_ops_auth(monkeypatch) -> None:
    monkeypatch.setenv("OPS_UI_ENABLED", "true")
    monkeypatch.setenv("OPS_UI_PASSWORD", "secret-pass")
    monkeypatch.setenv("OPS_UI_SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("OPS_UI_COOKIE_SECURE", "false")


def test_health_remains_public_when_ops_auth_enabled(monkeypatch) -> None:
    _configure_ops_auth(monkeypatch)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_protected_api_requires_login_and_keeps_cors_headers(monkeypatch) -> None:
    _configure_ops_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/api/template-posters",
        headers={"Origin": "https://zhaojfifa.github.io", "X-Request-ID": "req-auth-1"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "ops_auth_required"
    assert response.headers["access-control-allow-origin"]
    assert response.headers["x-request-id"] == "req-auth-1"


def test_ops_login_me_and_logout_flow(monkeypatch) -> None:
    _configure_ops_auth(monkeypatch)
    client = TestClient(app)

    wrong = client.post(
        "/api/auth/ops-login",
        json={"username": "ops", "password": "wrong"},
    )
    assert wrong.status_code == 401
    assert wrong.json()["authenticated"] is False

    login = client.post(
        "/api/auth/ops-login",
        json={"username": "ops", "password": "secret-pass"},
    )
    assert login.status_code == 200
    assert login.json()["authenticated"] is True
    assert login.json()["username"] == "ops"
    assert "HttpOnly" in login.headers["set-cookie"]

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json() == {
        "enabled": True,
        "authenticated": True,
        "username": "ops",
    }

    protected = client.get("/api/template-posters")
    assert protected.status_code == 200
    assert "posters" in protected.json()

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.json()["authenticated"] is False

    after_logout = client.get("/api/template-posters")
    assert after_logout.status_code == 401
