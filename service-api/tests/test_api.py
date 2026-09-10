"""Unit tests for service-api."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app, _store


@pytest.fixture(autouse=True)
def reset_store():
    """Isolate each test with a fresh store."""
    _store._index.reset()
    _store._docs.clear()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


def test_health_empty_store(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["docs_indexed"] == 0


def test_add_documents(client):
    r = client.post("/documents", json={"documents": ["doc1", "doc2"]})
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_query_empty_store_422(client):
    r = client.post("/query", json={"question": "test?"})
    assert r.status_code == 422


def test_query_with_docs(client):
    client.post("/documents", json={"documents": [
        "Python is a programming language.",
        "FastAPI is a web framework.",
    ]})
    r = client.post("/query", json={"question": "What is Python?"})
    assert r.status_code == 200
    assert "context" in r.json()


def test_health_reflects_doc_count(client):
    client.post("/documents", json={"documents": ["a", "b", "c"]})
    r = client.get("/health")
    assert r.json()["docs_indexed"] == 3


def test_gateway_forwards_uploaded_context(client, monkeypatch, mocker):
    import app.main as gateway
    monkeypatch.setattr(gateway, "_rag_service_url", "http://rag/query")
    client.post("/documents", json={"documents": ["The project codename is Nimbus-731."]})
    response = mocker.Mock()
    response.json.return_value = {"answer": "Nimbus-731", "context": ["wrong store"]}
    post = mocker.patch("app.main.httpx.post", return_value=response)
    result = client.post("/query", json={"question": "What is the project codename?"})
    expected = ["The project codename is Nimbus-731."]
    assert post.call_args.kwargs["json"]["context"] == expected
    assert result.json()["context"] == expected


def test_gateway_reports_generation_failure(client, monkeypatch, mocker):
    import app.main as gateway
    import httpx
    monkeypatch.setattr(gateway, "_rag_service_url", "http://rag/query")
    client.post("/documents", json={"documents": ["local document"]})
    mocker.patch("app.main.httpx.post", side_effect=httpx.ConnectError("offline"))
    result = client.post("/query", json={"question": "document"}).json()
    assert result["generation_status"] == "unavailable"
    assert result["context"] == ["local document"]
