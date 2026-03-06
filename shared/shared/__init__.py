"""Shared RAG library — public embedder module."""
from .embedder import SimpleEmbedder
from .vector_store import VectorStore

__all__ = ["SimpleEmbedder", "VectorStore"]
