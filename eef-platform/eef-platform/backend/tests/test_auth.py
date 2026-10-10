def test_login_success(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@12345"})
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "ADMIN"
    assert body["access_token"]


def test_login_wrong_password(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["success"] is False
    assert r.json()["error_code"] == "HTTP_401"


def test_login_unknown_user(client):
    r = client.post("/api/v1/auth/login", data={"username": "nobody", "password": "x"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_token(client, admin_token):
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_viewer_cannot_run_verification(client, viewer_token, demo_dir):
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as doc, \
         open(f"{demo_dir}/images/face_a_1.png", "rb") as selfie:
        r = client.post(
            "/api/v1/identity/verify",
            headers={"Authorization": f"Bearer {viewer_token}"},
            data={"full_name": "Test Person", "document_type": "NATIONAL_ID"},
            files={"document": ("doc.png", doc, "image/png"), "selfie": ("selfie.png", selfie, "image/png")},
        )
    assert r.status_code == 403
    assert r.json()["success"] is False


def test_viewer_can_read_platform_data_but_cannot_mutate(client, viewer_token):
    headers = {"Authorization": f"Bearer {viewer_token}"}
    read_paths = [
        "/api/v1/dashboard/stats",
        "/api/v1/identity?limit=5",
        "/api/v1/fraud/cases",
        "/api/v1/alerts",
        "/api/v1/graph/analytics",
        "/api/v1/audit",
        "/api/v1/models/status",
    ]

    for path in read_paths:
        assert client.get(path, headers=headers).status_code == 200, path

    assert client.post("/api/v1/fraud/scan", headers=headers).status_code == 403
    assert client.post("/api/v1/fraud/cases/1/notes", headers=headers, json={"note": "No edit"}).status_code == 403
    assert client.patch("/api/v1/alerts/1/status", headers=headers, json={"status": "RESOLVED"}).status_code == 403
    assert client.patch("/api/v1/fraud/cases/1/status", headers=headers, json={"status": "CLOSED"}).status_code == 403


def test_api_rate_limit_returns_structured_error(client, viewer_token, monkeypatch):
    from app import main
    from app.core.config import settings
    from app.core.rate_limit import RequestRateLimiter

    monkeypatch.setattr(main, "rate_limiter", RequestRateLimiter())
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 1)
    headers = {"Authorization": f"Bearer {viewer_token}"}

    assert client.get("/api/v1/models/status", headers=headers).status_code == 200
    response = client.get("/api/v1/models/status", headers=headers)

    assert response.status_code == 429
    assert response.json()["error_code"] == "RATE_LIMITED"
    assert response.headers["Retry-After"] == "60"


def test_unauthorized_access_to_users_list(client):
    r = client.get("/api/v1/users")
    assert r.status_code == 401
