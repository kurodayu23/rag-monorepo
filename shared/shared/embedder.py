"""Text embedder — converts strings to L2-normalised float32 vectors."""
from __future__ import annotations

import numpy as np


class SimpleEmbedder:
    """Deterministic, hash-based text embedder (no model weights needed)."""

    DIM: int = 64

    def encode(self, text: str) -> np.ndarray:
        # Python's built-in `hash()` is salted per-process, so vectors change across runs.
        # Use a stable hash (SHA256) to keep retrieval deterministic between processes/CI runs.
        import hashlib

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], byteorder="big", signed=False) % (2**31)
        rng = np.random.default_rng(seed)
        vec = rng.random(self.DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-9)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.encode(t) for t in texts])
