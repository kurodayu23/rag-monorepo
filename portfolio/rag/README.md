## LangChain RAG 示例（Ollama + Chroma）

这个目录的目的很简单：让你在面试时能清楚讲到“RAG + LangChain”这条链路，而不是把核心逻辑藏在服务里。

### 运行前准备

1. 确保本地有 Ollama
   - `ollama serve`
2. 安装依赖（示例）
   - `pip install langchain langchain-community langchain-core chromadb`

> embeddings 这里默认用 `HuggingFaceEmbeddings(all-MiniLM-L6-v2)`，如果你机器没网会失败；你可以换成本地可用的 embedding 配置。

### 简单用法

```python
from langchain_rag import LangChainRAGPipeline

rag = LangChainRAGPipeline(
    persist_directory="./chroma_db",
    ollama_model="gemma:4b",
)

print(rag.query("FAISS 在向量检索里有什么作用？", top_k=3))
```

### 面试讲解要点

- `Chroma`：向量存储与 Top-K 检索
- `create_retrieval_chain`：把“检索”和“生成”串成一条链
- `Ollama`：LLM 端用本地推理，避免云端 API key

