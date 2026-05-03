import pytest
import io
from fastapi.testclient import TestClient

def test_upload_invalid_type(client):
    file_content = b"fake content"
    file = io.BytesIO(file_content)
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("test.txt", file, "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_upload_valid_pdf(client):
    # Create a minimal valid-ish PDF header
    file_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Test) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    file = io.BytesIO(file_content)
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("test.pdf", file, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "File uploaded and classified successfully"
    assert data["metadata"]["file_type"] in ["digital_pdf", "scanned_pdf"]
    assert "document_id" in data["metadata"]
    return data["metadata"]["document_id"]
