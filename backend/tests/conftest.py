import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import limiter

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
limiter.enabled = False


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


DEFAULT_USER = {
    "password": "supersecret123",
    "age": 28,
    "city": "Wien",
    "gender": "mann",
    "interest": "frau",
    "gym": "John Harris Fitness",
    "consent_sensitive_data": True,
    "consent_withdrawal_waiver": True,
}


def register_user(client, email, name="Test User", **overrides):
    payload = {**DEFAULT_USER, "email": email, "name": name, **overrides}
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_admin(client, email="admin@example.com", password="adminsecret123", name="Admin"):
    """Legt einen AdminUser direkt in der DB an (kein öffentlicher Registrierungs-
    Endpoint vorgesehen) und loggt sich darüber ein."""
    from app.models import AdminUser
    from app.security import hash_password

    db = TestingSessionLocal()
    try:
        admin = AdminUser(email=email, password_hash=hash_password(password), name=name)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id
    finally:
        db.close()

    resp = client.post("/api/admin/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, admin_id
