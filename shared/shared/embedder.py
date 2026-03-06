"""Text embedder — converts strings to L2-normalised float32 vectors."""
from __future__ import annotations

import numpy as np


class SimpleEmbedder:
    """Deterministic, hash-based text embedder (no model weights needed)."""

    DIM: int = 64

    def encode(self, text: str) -> np.ndarray:
        rng = np.random.default_rng(abs(hash(text)) % (2**31))
        vec = rng.random(self.DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-9)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.encode(t) for t in texts])
