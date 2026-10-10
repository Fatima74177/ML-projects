import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///./eef_test.db"

from app.core.database import Base, engine, SessionLocal, init_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models._all import User  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    if os.path.exists("./eef_test.db"):
        os.remove("./eef_test.db")
    init_db()
    db = SessionLocal()
    db.add(User(username="admin", email="admin@test.local", full_name="Admin",
                 hashed_password=hash_password("Admin@12345"), role="ADMIN"))
    db.add(User(username="analyst", email="analyst@test.local", full_name="Analyst",
                 hashed_password=hash_password("Analyst@12345"), role="ANALYST"))
    db.add(User(username="viewer", email="viewer@test.local", full_name="Viewer",
                 hashed_password=hash_password("Viewer@12345"), role="VIEWER"))
    db.commit()
    db.close()
    yield
    engine.dispose()
    if os.path.exists("./eef_test.db"):
        os.remove("./eef_test.db")


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def _login(client, username, password):
    r = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(client):
    return _login(client, "admin", "Admin@12345")


@pytest.fixture(scope="session")
def analyst_token(client):
    return _login(client, "analyst", "Analyst@12345")


@pytest.fixture(scope="session")
def viewer_token(client):
    return _login(client, "viewer", "Viewer@12345")


@pytest.fixture(scope="session")
def demo_dir():
    return os.path.join(os.path.dirname(__file__), "..", "..", "data", "demo")
