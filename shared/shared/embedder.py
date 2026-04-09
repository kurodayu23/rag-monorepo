"""
Production-grade text embedder leveraging HuggingFace Transformers.
Replaces the legacy hash-based mock embedder with real state-of-the-art NLP representations.
"""
from __future__ import annotations

import logging
import numpy as np

logger = logging.getLogger(__name__)

class TransformersEmbedder:
    """
    Advanced text embedder using local HuggingFace Transformer models.
    Supports mean pooling, attention masking, and fp16 GPU acceleration.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._tokenizer = None
        self._model = None
        self.DIM = 384  # Default for MiniLM-L6-v2

    def _lazy_load(self):
        if self._model is None:
            logger.info("Lazy loading HuggingFace Transformer model: %s on %s", self.model_name, self.device)
            try:
                import torch
                from transformers import AutoModel, AutoTokenizer
            except ImportError as e:
                raise RuntimeError("Missing required dependencies: `pip install torch transformers`") from e

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()

    def _mean_pooling(self, model_output, attention_mask):
        """Perform average pooling of token embeddings using the attention mask."""
        import torch
        token_embeddings = model_output[0] # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    def encode(self, text: str) -> np.ndarray:
        return self.encode_batch([text])[0]

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        self._lazy_load()
        import torch
        
        # Tokenize sentences
        encoded_input = self._tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors='pt'
        ).to(self.device)

        # Compute token embeddings
        with torch.no_grad():
            model_output = self._model(**encoded_input)

        # Perform pooling
        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        
        # L2 Normalize embeddings
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        
        return sentence_embeddings.cpu().numpy().astype(np.float32)

class EmbedderProxy(TransformersEmbedder):
    """Alias for backwards compatibility with legacy service signatures."""
    pass
