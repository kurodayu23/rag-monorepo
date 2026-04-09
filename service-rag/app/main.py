"""RAG query service — supports native Ollama and optional LangChain engine."""
from __future__ import annotations

import os
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
    response = ollama.chat(model=_MODEL, messages=[{"role": "user", "content": prompt}])
    return {
        "question": question,
        "context": context,
        "answer": response["message"]["content"],
        "engine": "native",
    }
