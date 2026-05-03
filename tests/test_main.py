import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import os

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tender_ai.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_tender_ai.db"):
        os.remove("./test_tender_ai.db")

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_summary(client):
    response = client.get("/api/v1/reporting/summary")
    assert response.status_code == 200
    assert "total_documents" in response.json()
