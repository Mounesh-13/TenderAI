import pytest
import io
import time
import os
from fastapi.testclient import TestClient
from fpdf import FPDF

@pytest.fixture
def auth_token(client):
    # Register and login to get token
    client.post("/api/v1/auth/register", json={
        "email": "tester@tender.ai",
        "password": "securepassword123",
        "full_name": "QA Engine",
        "role": "admin"
    })
    response = client.post("/api/v1/auth/login", data={
        "username": "tester@tender.ai",
        "password": "securepassword123"
    })
    return response.json()["access_token"]

def create_test_pdf(text_content: str, filename: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text_content)
    pdf_output = io.BytesIO()
    pdf_str = pdf.output(dest='S')
    return io.BytesIO(pdf_str)

def test_full_system_lifecycle(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 1. Generate & Upload Test Tender
    tender_text = """
    TENDER FOR CLOUD SERVICES
    Requirement 1: Technical Infrastructure
    The bidder must have at least 5 years of experience in cloud deployments.
    Requirement 2: Financial Turnover
    The annual turnover of the bidder must be at least 10 Crore INR.
    Requirement 3: Compliance
    Bidder must be ISO 27001 certified.
    """
    tender_file = create_test_pdf(tender_text, "tender.pdf")
    
    response = client.post(
        "/api/v1/ingestion/upload?doc_type=tender",
        headers=headers,
        files={"file": ("tender.pdf", tender_file, "application/pdf")}
    )
    assert response.status_code == 200
    tender_id = response.json()["metadata"]["document_id"]

    # 2. Run Tender Pipeline (Criteria Extraction)
    client.post(f"/api/v1/pipelines/process/{tender_id}", headers=headers)
    time.sleep(3) # Wait for LLM/Background task

    # 3. Generate & Upload Test Bidder
    bidder_text = """
    BIDDER RESPONSE: TECH SOLUTIONS LTD
    Experience: We have 8 years of experience in cloud deployments.
    Turnover: Our annual turnover for FY 2025 is 15 Crore.
    Certification: We hold a valid ISO 27001 certificate.
    """
    bidder_file = create_test_pdf(bidder_text, "bidder.pdf")
    
    response = client.post(
        f"/api/v1/ingestion/upload?doc_type=bidder&parent_tender_id={tender_id}",
        headers=headers,
        files={"file": ("bidder.pdf", bidder_file, "application/pdf")}
    )
    assert response.status_code == 200
    bidder_id = response.json()["metadata"]["document_id"]

    # 4. Run Bidder Pipeline (Evaluation & Evidence)
    client.post(f"/api/v1/pipelines/process/{bidder_id}", headers=headers)
    time.sleep(4) # Wait for Evaluation

    # 5. VALIDATION: Check Final Report
    response = client.get(f"/api/v1/reporting/report/{bidder_id}", headers=headers)
    assert response.status_code == 200
    report = response.json()

    # Validate criteria extraction
    # (If LLM mock is on, it might return generic ones, but we check presence)
    assert "tender_benchmarks" in report
    assert len(report["tender_benchmarks"]) > 0

    # Validate evaluation works
    assert "ai_evaluation" in report
    assert report["ai_evaluation"]["overall_score"] >= 0.0

    # Validate evidence generated
    assert "evidence_chains" in report
    assert len(report["evidence_chains"]) > 0
    # Check for human-readable format
    assert "→" in report["evidence_chains"][0]["summary"]

    # 6. Audit Trail Verification
    response = client.get(f"/api/v1/audit/trail/{bidder_id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["logs"]) > 0
    # Check for BIDDER_EVALUATED action
    actions = [log["action"] for log in response.json()["logs"]]
    assert any("BIDDER" in a for a in actions)
