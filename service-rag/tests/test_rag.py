"""Unit tests for service-rag."""
from __future__ import annotations

import pytest
from app.main import query, _store


def test_query_returns_dict(mocker):
    mocker.patch("app.main.ollama.chat",
                 return_value={"message": {"content": "FAISS is fast."}})
    result = query("What is FAISS?")
    assert isinstance(result, dict)
    assert "question" in result
    assert "context" in result
    assert "answer" in result


def test_query_context_not_empty(mocker):
    mocker.patch("app.main.ollama.chat",
                 return_value={"message": {"content": "ok"}})
    result = query("FAISS vector search")
    assert len(result["context"]) > 0


def test_no_real_llm_call(mocker):
    """Ensure no real Ollama HTTP requests are made during CI."""
    mock = mocker.patch("app.main.ollama.chat",
                        return_value={"message": {"content": "mocked"}})
    query("test question")
    mock.assert_called_once()


def test_top_k_limits_context(mocker):
    mocker.patch("app.main.ollama.chat",
                 return_value={"message": {"content": "ok"}})
    result = query("anything", top_k=1)
    assert len(result["context"]) == 1


def test_store_preloaded():
    """Shared vector store has pre-loaded documents."""
    assert _store.count >= 5
