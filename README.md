[English](README.md) | [简体中文](README_zh.md)

---

# RAG Monorepo / VibeOps Interview Platform

这不是“堆技术名词”的 README。它是一套面试用的工程化展示：每个能力都能在目录里找到对应代码，并且能跑通关键链路。

## What this repo demonstrates / 你会在这里看到什么

- `shared/`: deterministic embedder + FAISS vector store (CI friendly)
- `service-api/`: FastAPI gateway (documents + query)
- `service-rag/`: answer engine (native Ollama, optional LangChain)
- `.teamcity/`: TeamCity Kotlin DSL CI/CD (pipeline-as-code)
- `integration_tests/`: end-to-end tests (docker-compose)
- `portfolio/`: interview-focused modules (agent / async / AIGC / Django API / LangChain RAG)

## Layout

```text
rag-monorepo/
├── shared/
├── service-api/
├── service-rag/
├── integration_tests/
├── .teamcity/
├── docker-compose.integration.yml
└── portfolio/
```

## Quick start: run the RAG loop locally

### 1) Start services

```bash
docker compose -f docker-compose.integration.yml up --build
```

- `service-api`: `http://localhost:8000`
- `service-rag`: `http://localhost:8001`

### 2) Add documents

```bash
curl -X POST http://localhost:8000/documents ^
  -H "Content-Type: application/json" ^
  -d "{\"documents\":[\"FAISS 用于向量相似度检索。\",\"Ollama 用于本地推理。\"]}"
```

### 3) Query

```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"FAISS 是什么？\",\"top_k\":3}"
```

Notes:
- When Ollama is available, `service-rag` will generate an answer.
- When Ollama is not available, it falls back to a context-backed response (so demos/CI don't hang).

## Engine switch (service-rag)

- `RAG_ENGINE=native` (default): direct Ollama call
- `RAG_ENGINE=langchain`: LangChain chain construction

## Local test order

```bash
cd shared && poetry install && poetry run pytest -q
cd ../service-rag && poetry install && poetry run pytest -q
cd ../service-api && poetry install && poetry run pytest -q
cd .. && pytest integration_tests -q
```

## portfolio: interview-focused modules

- `portfolio/agent/`: small agent CLI (Qt annotation + async harvesting)
- `portfolio/aigc/`: Midjourney prompt templates + SD ControlNet sample
- `portfolio/rag/`: LangChain RAG sample (Ollama + Chroma)
- `portfolio/django_api/`: Django API proxy design (to `service-api`)

Agent CLI examples:

```bash
python -m portfolio.agent.cli annotate-qt --file "path/to/YourFile.cpp" --model gemma2:9b
python -m portfolio.agent.cli harvest --range 50 --concurrency 20
```

## License

MIT
