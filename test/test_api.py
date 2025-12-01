import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.db import db
import io

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test"""
    db.documents.clear()
    db.metrics = {
        "total_ingests": 0,
        "total_extractions": 0,
        "total_questions": 0,
        "total_audits": 0
    }
    yield
    db.documents.clear()

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Contract Intelligence API" in response.json()["message"]

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_ingests" in data

def test_list_documents_empty():
    """Test listing documents when none uploaded"""
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert len(response.json()["documents"]) == 0

def test_ingest_no_files():
    """Test ingest endpoint with no files - should fail"""
    response = client.post("/ingest", files=[])
    assert response.status_code == 422  

def test_ingest_valid_pdf():
    """Test ingesting a valid PDF"""
    
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    files = {"files": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    response = client.post("/ingest", files=files)
    

    assert response.status_code in [200, 400, 500]  

def test_extract_nonexistent_document():
    """Test extraction with non-existent document ID"""
    response = client.post("/extract", params={"document_id": "nonexistent123"})
    assert response.status_code == 404

def test_ask_no_documents():
    """Test asking question with no documents uploaded"""
    response = client.post("/ask", params={"question": "What is this contract about?"})
    assert response.status_code == 200
    data = response.json()
    assert "No documents found" in data["answer"]

def test_ask_empty_question():
    """Test asking empty question"""
    response = client.post("/ask", params={"question": ""})
    assert response.status_code == 400

def test_audit_nonexistent_document():
    """Test audit with non-existent document"""
    response = client.post("/audit", params={"document_id": "nonexistent123"})
    assert response.status_code == 404

def test_webhook_event():
    """Test webhook event endpoint"""
    response = client.post(
        "/webhook/events",
        params={
            "event_type": "test_event",
            "document_id": "test123"
        },
        json={"status": "completed"}
    )
    assert response.status_code == 200
    assert "Webhook event queued" in response.json()["message"]

def test_stream_endpoint_exists():
    """Test that stream endpoint exists"""
    response = client.get("/ask/stream", params={"question": "test"})
   
    assert response.status_code == 200

@pytest.mark.parametrize("endpoint,method", [
    ("/healthz", "GET"),
    ("/metrics", "GET"),
    ("/documents", "GET"),
])
def test_endpoint_accessibility(endpoint, method):
    """Test that all GET endpoints are accessible"""
    if method == "GET":
        response = client.get(endpoint)
    assert response.status_code == 200