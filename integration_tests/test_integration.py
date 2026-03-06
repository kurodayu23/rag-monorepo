"""Integration tests — hit live API service endpoints."""
from __future__ import annotations

import httpx
import pytest

BASE = "http://localhost:8000"


def test_health():
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_add_and_query():
    httpx.post(f"{BASE}/documents", json={"documents": [
        "FAISS is a vector search library.",
        "RAG improves LLM accuracy.",
    ]})
    r = httpx.post(f"{BASE}/query", json={"question": "What is FAISS?"})
    assert r.status_code == 200
    assert len(r.json()["context"]) > 0
