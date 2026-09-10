"""使用本地 Transformer 模型生成归一化文本向量。"""
from __future__ import annotations

import logging
import numpy as np

logger = logging.getLogger(__name__)

class TransformersEmbedder:
    """MiniLM 默认输出 384 维向量，模型在首次编码时加载。"""

    DIM = 384

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._tokenizer = None
        self._model = None

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
            self.DIM = self._model.config.hidden_size

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
        if not texts:
            return np.empty((0, self.DIM), dtype=np.float32)
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

# 保留原有公开导入名称，统一使用同一个实现。
SimpleEmbedder = TransformersEmbedder
EmbedderProxy = TransformersEmbedder
