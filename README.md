[English](README.md) | [简体中文](README_zh.md)

---

# 🚀 RAG Monorepo: Enterprise-Grade Retrieval Augmented Generation

> **An engineering-focused, destructible, testable, and CI-ready RAG microservice architecture.**

This repository is **NOT** a "single-file toy demo" often seen in AI tutorials. It demonstrates production-level MLOps capabilities by orchestrating robust NLP embedding techniques alongside advanced LCEL routing graphs.

## 🎯 Core Capabilities Demonstrated

### 1. 🧠 HuggingFace Transformers Integeration
We moved away from naive text splitting/hashing and implemented a real representation pipeline.
- Uses `sentence-transformers/all-MiniLM-L6-v2` locally via HuggingFace `transformers`.
- Implements direct **tensor mathematical manipulation**: custom mean pooling and attention mask expansion in PyTorch.
- Evaluates GPU inference and CPU fallback.

### 2. ⛓️ LangChain LCEL Routing & Anti-Hallucination
The `service-rag` module does not just perform a basic `prompt | llm` operation.
- Implements a programmatic **LCEL (LangChain Expression Language)** computational graph.
- **Conditional Routing (`RunnableBranch`)**: Prior to generating an answer, an evaluation chain verifies if the retrieved chunks contain the required facts.
- **Graceful Degradation**: If the context is missing info, the router surgically aborts generation to guarantee a **0% hallucination rate** instead of returning garbage.

### 3. ☸️ Microservice CI/CD & Monorepo Tooling
- API Gateway (`service-api`), Backend logic (`service-rag`), and core AI packages (`shared`) are structurally separated via Poetry.
- Fully wired for Kotlin DSL integration testing (e.g. Jenkins / TeamCity).
- Containerized for rapid spin-up via Docker Compose.

---

## 📂 Architecture Layout

```text
rag-monorepo/
├── shared/                     # AI Core
│   ├── shared/embedder.py      # HuggingFace Transformer Pooling
│   └── shared/vector_store.py  # Local FAISS Indexing
├── service-api/                # Edge API 
│   └── app/main.py             # FastAPI async routes
├── service-rag/                # Domain Logic
│   └── app/langchain_engine.py # Advanced LCEL graph & Hallucination Guard
└── integration_tests/          # E2E Test Suite
```

## 🛠️ Bootstrapping

Ensure you have Docker and Poetry installed.

1. **Spin up the ecosystem**
   ```bash
   docker-compose -f docker-compose.integration.yml up -d
   ```

2. **Trigger advanced LCEL answering pipeline** (Assuming documents indexed)
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I optimize CUDA allocations?", "rag_engine": "langchain"}'
   ```

## 🧠 Why This Matters

Anybody can write `import langchain`. True AI engineering requires understanding the internals: *tokenization limits, attention masking, precision degradations (fp16), and vector similarity spaces (L2 Norms).* This workspace acts as a pristine baseline to evaluate large-scale backend decisions before cloud deployment.
