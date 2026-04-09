"""RAG query service — HTTP API for retrieval + generation (native Ollama, optional LangChain)."""
from __future__ import annotations

import os
from fastapi import FastAPI
from pydantic import BaseModel, Field

import ollama
from shared import VectorStore

from app.langchain_engine import query_with_langchain

_store = VectorStore()

# Pre-load sample knowledge base
_store.add([
    "FAISS is a library for efficient similarity search and clustering of dense vectors.",
    "Ollama runs large language models locally without cloud dependency.",
    "RAG (Retrieval-Augmented Generation) improves LLM accuracy by grounding it in retrieved facts.",
    "Poetry manages Python dependencies using pyproject.toml and a lock file.",
    "TeamCity supports Kotlin DSL for pipeline-as-code configuration.",
])

_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
_ENGINE = os.getenv("RAG_ENGINE", "native").lower()  # native | langchain

app = FastAPI(title="service-rag", version="1.0.0")


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "docs_indexed": _store.count}


def query(question: str, top_k: int = 3) -> dict:
    """Retrieve context and generate an answer."""
    context = _store.search(question, k=top_k)
    if not context:
        return {"question": question, "context": [], "answer": "No context available."}

    if _ENGINE == "langchain":
        answer = query_with_langchain(question=question, context=context, model_name=_MODEL)
        return {
            "question": question,
            "context": context,
            "answer": answer,
            "engine": "langchain",
        }

    prompt = (
        "Answer based only on the context below.\n\n"
        "Context:\n" + "\n".join(f"- {c}" for c in context) +
        f"\n\nQuestion: {question}\nAnswer:"
    )
    try:
        response = ollama.chat(model=_MODEL, messages=[{"role": "user", "content": prompt}])
        answer = response["message"]["content"]
    except Exception as e:
        # CI / portfolio demo friendliness:
        # If Ollama isn't reachable, keep the service usable by returning a context-backed fallback.
        answer = f"Ollama unavailable ({type(e).__name__}). Returning retrieved context only."
    return {
        "question": question,
        "context": context,
        "answer": answer,
        "engine": "native",
    }


@app.post("/query")
def query_endpoint(body: QueryRequest) -> dict:
    return query(question=body.question, top_k=body.top_k)


if __name__ == "__main__":
    # Local dev convenience: `python -m app.main`
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
