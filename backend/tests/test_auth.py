import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.seed import ensure_default_user


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "test-secret")
    monkeypatch.setattr(settings, "allow_signup", True)   # most tests create accounts
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    c = TestClient(app)   # no "with": the real startup (and your real finpilot.db) is never touched
    c.Session = Session   # lets tests use the same throwaway database directly
    yield c
    app.dependency_overrides.clear()


def signup(client, email="a@x.com"):
    r = client.post("/auth/register", json={"name": "Ann", "email": email, "password": "password123"})
    assert r.status_code == 200, r.text
    return r.json()


def test_register_and_login(client):
    data = signup(client)
    assert data["token"]
    assert data["businesses"][0]["name"] == "My Business"
    r = client.post("/auth/login", json={"email": "a@x.com", "password": "password123"})
    assert r.status_code == 200
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['token']}"})
    assert r.json()["user"]["email"] == "a@x.com"


def test_wrong_password_is_rejected(client):
    signup(client)
    r = client.post("/auth/login", json={"email": "a@x.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_data_routes_require_login(client):
    r = client.get("/transactions", headers={"X-Business-Id": "1"})
    assert r.status_code == 401


def test_user_cannot_read_another_users_business(client):
    a = signup(client, "a@x.com")
    b = signup(client, "b@x.com")
    biz_a = a["businesses"][0]["id"]
    r = client.get("/transactions", headers={"Authorization": f"Bearer {b['token']}",
                                             "X-Business-Id": str(biz_a)})
    assert r.status_code == 404


def test_signup_is_blocked_when_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_signup", False)
    r = client.post("/auth/register", json={"name": "Eve", "email": "eve@x.com", "password": "password123"})
    assert r.status_code == 403


def test_fixed_default_login(client, monkeypatch):
    monkeypatch.setattr(settings, "default_email", "user@gmail.com")
    monkeypatch.setattr(settings, "default_password", "1234")
    with client.Session() as db:
        ensure_default_user(db)
        ensure_default_user(db)   # running twice must not create a duplicate account
    r = client.post("/auth/login", json={"email": "user@gmail.com", "password": "1234"})
    assert r.status_code == 200, r.text
    assert len(r.json()["businesses"]) == 1
    r = client.post("/auth/login", json={"email": "user@gmail.com", "password": "12345"})
    assert r.status_code == 401