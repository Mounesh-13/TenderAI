import pytest
import io
import time
from fastapi.testclient import TestClient

@pytest.fixture
def auth_token(client):
    # Register and login to get token
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User",
        "role": "admin"
    })
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    return response.json()["access_token"]

def test_end_to_end_pipeline(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 1. Upload Tender Document
    tender_file = io.BytesIO(b"Tender for IT Services. Turnover required must be at least 5 Cr.")
    response = client.post(
        "/api/v1/ingestion/upload?doc_type=tender",
        headers=headers,
        files={"file": ("tender.pdf", tender_file, "application/pdf")}
    )
    assert response.status_code == 200
    tender_id = response.json()["metadata"]["document_id"]

    # 2. Upload Bidder Document
    bidder_file = io.BytesIO(b"Bidder Profile. Annual turnover is INR 7 Crore.")
    response = client.post(
        f"/api/v1/ingestion/upload?doc_type=bidder&parent_tender_id={tender_id}",
        headers=headers,
        files={"file": ("bidder.pdf", bidder_file, "application/pdf")}
    )
    assert response.status_code == 200
    bidder_id = response.json()["metadata"]["document_id"]

    # 3. Process Tender (Extract Criteria)
    # Note: This will use the mock path if Gemini API key is missing
    response = client.post(f"/api/v1/pipelines/process/{tender_id}", headers=headers)
    assert response.status_code == 200
    
    # Wait for background task (simplified for test)
    time.sleep(2)

    # 4. Process Bidder (Evaluate)
    response = client.post(f"/api/v1/pipelines/process/{bidder_id}", headers=headers)
    assert response.status_code == 200
    
    # Wait for background task
    time.sleep(3)

    # 5. Validate Report
    response = client.get(f"/api/v1/reporting/report/{bidder_id}", headers=headers)
    assert response.status_code == 200
    report = response.json()
    
    assert report["report_metadata"]["document_id"] == bidder_id
    assert "ai_evaluation" in report
    assert "evidence_chains" in report
    assert len(report["evidence_chains"]) > 0
    
    # 6. HITL Review
    review_request = {
        "document_id": bidder_id,
        "reviewer_id": "test-user-id", # This should ideally be a real ID from DB
        "decision": "ELIGIBLE",
        "reason": "Verified turnover documents manually.",
        "corrections": []
    }
    # Need to get a real user ID for reviewer_id to pass foreign key check
    me = client.get("/api/v1/auth/me", headers=headers).json()
    review_request["reviewer_id"] = me["id"]
    
    response = client.post("/api/v1/hitl/review", headers=headers, json=review_request)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    # 7. Final Check
    response = client.get(f"/api/v1/reporting/report/{bidder_id}", headers=headers)
    assert response.json()["report_metadata"]["status"] == "completed"
    assert response.json()["expert_review"]["decision"] == "ELIGIBLE"
