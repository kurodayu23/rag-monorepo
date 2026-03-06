"""FAISS-backed vector store."""
from __future__ import annotations

import numpy as np
import faiss  # type: ignore[import-untyped]

from .embedder import SimpleEmbedder


class VectorStore:
    def __init__(self, dim: int = SimpleEmbedder.DIM) -> None:
        self._index = faiss.IndexFlatL2(dim)
        self._docs: list[str] = []
        self._emb = SimpleEmbedder()

    def add(self, docs: list[str]) -> None:
        if not docs:
            return
        vecs = self._emb.encode_batch(docs)
        self._index.add(vecs)
        self._docs.extend(docs)

    def search(self, query: str, k: int = 3) -> list[str]:
        if self._index.ntotal == 0:
            return []
        vec = self._emb.encode(query).reshape(1, -1)
        k = min(k, self._index.ntotal)
        _, idxs = self._index.search(vec, k)
        return [self._docs[i] for i in idxs[0] if i >= 0]

    @property
    def count(self) -> int:
        return self._index.ntotal
