"""Integration tests for the SIH Platform backend."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

# Tests use a throwaway in-memory database so they stay self-contained (no MySQL
# required) and never create a .db file inside the project directory.
TEST_DB_URL = "sqlite://"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_auth_login_missing_body(client):
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 422


def test_auth_signup_missing_body(client):
    response = client.post("/api/auth/signup", json={})
    assert response.status_code == 422


def test_opportunities_empty_list(client):
    response = client.get("/api/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_opportunities_invalid_id(client):
    response = client.get("/api/opportunities/99999")
    assert response.status_code in (404, 400)


def test_analytics_skill_gap_no_profile(client):
    response = client.get("/api/analytics/student/skill-gap/99999")
    # Either 404 or a graceful error is acceptable; just assert it does not 500.
    assert response.status_code != 500
