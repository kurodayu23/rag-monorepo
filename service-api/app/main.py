"""FastAPI gateway — exposes RAG query and document management endpoints."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from shared import VectorStore

app = FastAPI(title="RAG Gateway API", version="1.0.0")
_store = VectorStore()


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
    # In production this calls service-rag via HTTP; here we return context directly
    return {"question": body.question, "context": context, "answer": "Retrieved from gateway."}
