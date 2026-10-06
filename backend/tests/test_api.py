import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "vector_store" in data
    assert "database" in data


def test_seed_and_list_documents():
    # Seed sample documents
    seed_res = client.post("/api/v1/documents/seed-samples")
    assert seed_res.status_code == 200

    # List documents
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 3

    # Check document fields
    doc = docs[0]
    assert "filename" in doc
    assert "chunk_count" in doc
    assert doc["chunk_count"] > 0
    assert doc["status"] == "indexed"


def test_retrieval_query():
    # Test direct retrieval
    payload = {
        "query": "What is the password rotation policy?",
        "top_k": 3,
        "enable_reranking": True,
    }
    response = client.post("/api/v1/retrieval/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    top_chunk = data["chunks"][0]
    assert "Enterprise_AI_Security_Policy" in top_chunk["filename"] or "password" in top_chunk["content"].lower()
    assert top_chunk["page_number"] >= 1


def test_chat_grounded_answer_and_citations():
    payload = {
        "message": "What is the monthly high-speed internet stipend amount?",
        "top_k": 4,
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "conversation_id" in data
    assert "assistant_message" in data
    assistant = data["assistant_message"]

    # Grounding & citation assertions
    assert assistant["is_grounded"] is True
    assert len(assistant["citations"]) > 0
    assert "$75" in assistant["content"] or "stipend" in assistant["content"].lower()


def test_chat_hallucination_refusal():
    # Out of scope question
    payload = {
        "message": "What is the corporate recipe for chocolate chip cookies in the office pantry?",
        "top_k": 4,
        "similarity_threshold": 0.5,
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assistant = data["assistant_message"]

    # Must refuse or indicate insufficient information
    refusal_keywords = ["not have enough information", "do not have enough information", "insufficient", "not contain enough"]
    assert any(k in assistant["content"].lower() for k in refusal_keywords) or not assistant["is_grounded"] or assistant["confidence"] == "unsupported"


def test_evaluation_run():
    response = client.post("/api/v1/eval/run")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]
    assert metrics["total_questions"] >= 5
    assert metrics["retrieval_hit_rate_pct"] >= 60.0
    assert metrics["citation_coverage_pct"] >= 60.0
    assert len(data["results"]) >= 5
