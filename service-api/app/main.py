"""FastAPI gateway — exposes RAG query and document management endpoints."""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from shared import VectorStore

app = FastAPI(title="RAG Gateway API", version="1.0.0")
_store = VectorStore()
_rag_service_url = os.getenv("RAG_SERVICE_URL")  # e.g. http://service-rag:8001/query


class AddDocsRequest(BaseModel):
    documents: list[str] = Field(..., min_length=1)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok", "docs_indexed": _store.count}


@app.post("/documents")
def add_documents(body: AddDocsRequest):
    _store.add(body.documents)
    return {"added": len(body.documents), "total": _store.count}


@app.post("/query")
def query(body: QueryRequest):
    if _store.count == 0:
        raise HTTPException(422, "Store is empty. Add documents first.")
    context = _store.search(body.question, k=body.top_k)
    # When configured, call service-rag so the answer is generated with LLM.
    if _rag_service_url:
        try:
            resp = httpx.post(
                _rag_service_url,
                json={"question": body.question, "top_k": body.top_k, "context": context},
                timeout=20.0,
            )
            resp.raise_for_status()
            payload = resp.json()
            # Keep context in sync even if rag service changes response shape.
            payload["context"] = context
            payload.setdefault("answer", "No answer returned by rag service.")
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            return {
                "question": body.question,
                "context": context,
                "answer": "Generation service unavailable; returning retrieved context only.",
                "generation_status": "unavailable",
                "error_type": type(exc).__name__,
            }

    return {
        "question": body.question,
        "context": context,
        "answer": "Retrieved from gateway (rag service not configured).",
    }
