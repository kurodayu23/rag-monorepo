"""Tests for the shared RAG library."""
from __future__ import annotations

import numpy as np
import pytest

from shared import SimpleEmbedder, VectorStore


class TestEmbedder:
    def test_output_dim(self):
        assert SimpleEmbedder().encode("hello").shape == (SimpleEmbedder.DIM,)

    def test_unit_norm(self):
        vec = SimpleEmbedder().encode("hello")
        assert abs(np.linalg.norm(vec) - 1.0) < 1e-5

    def test_deterministic(self):
        e = SimpleEmbedder()
        assert np.allclose(e.encode("x"), e.encode("x"))

    def test_different_texts_differ(self):
        e = SimpleEmbedder()
        assert not np.allclose(e.encode("cat"), e.encode("dog"))

    def test_encode_batch_shape(self):
        result = SimpleEmbedder().encode_batch(["a", "b", "c"])
        assert result.shape == (3, SimpleEmbedder.DIM)


class TestVectorStore:
    def test_empty_search(self):
        assert VectorStore().search("anything") == []

    def test_add_and_count(self):
        vs = VectorStore()
        vs.add(["doc1", "doc2"])
        assert vs.count == 2

    def test_search_returns_results(self):
        vs = VectorStore()
        vs.add(["FAISS is fast", "Python is great", "RAG is useful"])
        results = vs.search("fast vector search", k=2)
        assert len(results) == 2

    def test_top_k_respected(self):
        vs = VectorStore()
        vs.add([f"doc {i}" for i in range(10)])
        assert len(vs.search("test", k=3)) == 3

    def test_add_empty_noop(self):
        vs = VectorStore()
        vs.add([])
        assert vs.count == 0
