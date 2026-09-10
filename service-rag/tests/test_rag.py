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


def test_langchain_engine_selected(monkeypatch, mocker):
    import app.main as rag_main
    monkeypatch.setattr(rag_main, "_ENGINE", "langchain")
    mocker.patch("app.main.query_with_langchain", return_value="from-lc")
    response = rag_main.query("What is FAISS?", top_k=1)
    assert response["engine"] == "langchain"
    assert response["answer"] == "from-lc"


def test_supplied_context_is_used_for_generation(mocker):
    chat = mocker.patch("app.main.ollama.chat", return_value={"message": {"content": "Nimbus"}})
    result = query("codename?", context=["codename: Nimbus"])
    assert result["context"] == ["codename: Nimbus"]
    assert "codename: Nimbus" in chat.call_args.kwargs["messages"][0]["content"]


def test_explicit_empty_context_does_not_use_sample_store(mocker):
    chat = mocker.patch("app.main.ollama.chat")
    result = query("anything", context=[])
    assert result["context"] == []
    chat.assert_not_called()
