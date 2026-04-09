[English](README.md) | [简体中文](README_zh.md)

---

# RAG Monorepo

Production-oriented monorepo for RAG services with pipeline-as-code.

## What this repo demonstrates

- Shared retrieval core (`shared/`)
- API gateway (`service-api/`)
- Generation service (`service-rag/`)
- TeamCity Kotlin DSL CI/CD (`.teamcity/settings.kts`)
- Integration orchestration with Docker Compose

## Layout

```text
rag-monorepo/
├── shared/              # embedder + vector store
├── service-api/         # FastAPI gateway
├── service-rag/         # native / LangChain answer engine
├── integration_tests/   # end-to-end tests
├── .teamcity/           # CI/CD as code (Kotlin DSL)
└── docker-compose.integration.yml
```

## Engine switch (service-rag)

- `RAG_ENGINE=native` (default): Ollama direct call
- `RAG_ENGINE=langchain`: LangChain chain construction

## Local test order

```bash
cd shared && poetry install && poetry run pytest -q
cd ../service-rag && poetry install && poetry run pytest -q
cd ../service-api && poetry install && poetry run pytest -q
cd .. && pytest integration_tests -q
```

## CI/CD

- TeamCity pipeline: unit tests -> integration -> docker build/push
- Trigger rules are path-based to avoid unnecessary builds.

## License

MIT
