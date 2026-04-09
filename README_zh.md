[English](README.md) | [简体中文](README_zh.md)

---

# RAG Monorepo：面向工程评审的检索增强生成项目

这个仓库不是“单文件 Demo”，而是一个可拆解、可测试、可接入 CI 的 RAG 多服务结构。

## 目标

用一个仓库同时展示以下能力：
- RAG 核心数据路径（向量化、检索、回答）
- LangChain 在服务内的可切换接入
- CI/CD Pipeline-as-Code（TeamCity Kotlin DSL）
- 集成测试与容器化联调

---

## 仓库结构

```text
rag-monorepo/
├── shared/
│   ├── shared/embedder.py      # 文本向量化
│   └── shared/vector_store.py  # FAISS 向量索引
├── service-api/
│   └── app/main.py             # FastAPI 网关
├── service-rag/
│   ├── app/main.py             # 查询主入口（native/langchain 切换）
│   └── app/langchain_engine.py # LangChain 组装逻辑
├── integration_tests/
│   └── test_integration.py     # 跨服务验证
├── .teamcity/settings.kts      # TeamCity Kotlin DSL
└── docker-compose.integration.yml
```

---

## RAG 引擎切换

`service-rag` 支持两种路径：

1. `RAG_ENGINE=native`（默认）
- 直接调用 Ollama
- 依赖最少，适合本地开发与 CI

2. `RAG_ENGINE=langchain`
- 用 LangChain 构建 prompt + model runnable
- 便于后续扩展多步骤链路（re-rank、tool call、memory）

这样做的目的不是“炫技”，而是把“可维护性”和“可替换性”提前设计进去。

---

## CI/CD 设计重点

`.teamcity/settings.kts` 中实现了：
- 按路径触发构建，减少无关流水线开销
- 单元测试与集成测试分层执行
- Docker 构建与推送阶段可参数化
- 失败时强制清理 compose 资源，防止脏环境污染后续任务

---

## 本地运行与测试

```bash
# shared
cd shared
poetry install
poetry run pytest -q

# service-rag
cd ../service-rag
poetry install
poetry run pytest -q

# service-api
cd ../service-api
poetry install
poetry run pytest -q

# integration
cd ..
pytest integration_tests -q
```

---

## 代码评审关注点

- `shared/vector_store.py`：向量存储接口是否足够稳定
- `service-rag/app/main.py`：引擎切换是否影响外部契约
- `.teamcity/settings.kts`：触发规则和依赖图是否避免无效构建

## License

MIT
