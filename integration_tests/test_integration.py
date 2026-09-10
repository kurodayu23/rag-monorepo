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
    # 网关首次编码会下载并加载 MiniLM，冷启动不能沿用 httpx 的 5 秒默认值。
    uploaded = httpx.post(f"{BASE}/documents", timeout=120, json={"documents": [
        "FAISS is a vector search library.",
        "The unique project codename is Nimbus-731.",
    ]})
    uploaded.raise_for_status()
    assert uploaded.json()["added"] == 2
    r = httpx.post(f"{BASE}/query", timeout=30, json={"question": "What is the unique project codename?"})
    assert r.status_code == 200
    assert len(r.json()["context"]) > 0

    assert "The unique project codename is Nimbus-731." in r.json()["context"]
