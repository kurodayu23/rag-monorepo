"""RAG query service — uses shared FAISS store + Ollama."""
from __future__ import annotations

import os
import ollama
from shared import VectorStore, SimpleEmbedder

_store = VectorStore()
_embedder = SimpleEmbedder()

# Pre-load sample knowledge base
_store.add([
    "FAISS is a library for efficient similarity search and clustering of dense vectors.",
    "Ollama runs large language models locally without cloud dependency.",
    "RAG (Retrieval-Augmented Generation) improves LLM accuracy by grounding it in retrieved facts.",
    "Poetry manages Python dependencies using pyproject.toml and a lock file.",
    "TeamCity supports Kotlin DSL for pipeline-as-code configuration.",
])

_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def query(question: str, top_k: int = 3) -> dict:
    """Retrieve context and generate an answer."""
    context = _store.search(question, k=top_k)
    if not context:
        return {"question": question, "context": [], "answer": "No context available."}

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
    }
