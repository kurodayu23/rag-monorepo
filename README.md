# RAG Monorepo

使用 FastAPI、MiniLM、FAISS 和 Ollama 构建的检索增强问答示例，包含共享向量库、API 网关、生成服务、测试和容器配置。

## Vibe Coding / AI 辅助开发

本项目采用 AI 辅助开发，通过需求描述与迭代反馈，使用 AI 辅助编写和修改代码。Vibe Coding 在这里描述开发方式；项目的具体功能与完成度以源码、运行说明和验证记录为准。

项目本身集成文本嵌入、向量检索与大模型调用。展示重点是上下文传递、生成路由、服务通信与集成测试。

维护时以明确需求、审查代码改动和可复现验证为准；具体测试及尚未验证的部分见下方说明。

## 数据如何流动

`POST /documents` 把文档写入网关的内存向量库；`POST /query` 检索 top-k 文档，并将同一份上下文传给生成服务。生成服务使用 Ollama 回答，可通过 `RAG_ENGINE=langchain` 选择 LCEL 条件拒答管线。

- `shared/shared/embedder.py`：MiniLM 编码、attention mask 平均池化和向量归一化。保留 `SimpleEmbedder` 旧导入名，实际使用 Transformer。
- `shared/shared/vector_store.py`：FAISS L2 索引与文档映射。
- `service-api/app/main.py`：文档入口、检索和生成服务调用。
- `service-rag/app/main.py`：生成入口，直接调用时可使用内置示例文档。
- `service-rag/app/langchain_engine.py`：判断上下文是否充分，再回答或拒答。

## 运行

主要运行与 CI 验证环境为 Linux / Docker，使用 Python 3.11/3.12 和 Poetry 1.8.3。锁文件使用 CPU 版 PyTorch。第一次编码需要联网下载 `sentence-transformers/all-MiniLM-L6-v2`，后续使用本地缓存。

在各子目录分别安装依赖：

```bash
cd shared
poetry install
cd ../service-rag
poetry install --all-extras
poetry run uvicorn app.main:app --port 8001
```

另一个终端启动网关（以下环境变量语法适用于 Bash）：

```bash
cd service-api
poetry install
RAG_SERVICE_URL=http://localhost:8001/query poetry run uvicorn app.main:app --port 8000
```

PowerShell 中先执行 `$env:RAG_SERVICE_URL='http://localhost:8001/query'`，再运行相同的 `poetry run uvicorn` 命令。

如需真实生成，先启动本地 Ollama 并准备 `llama3`，或通过生成服务的 `OLLAMA_MODEL` 指定已安装模型。未启动 Ollama 时接口会明确返回仅检索结果，不代表生成成功。

```bash
curl -X POST http://localhost:8000/documents -H 'Content-Type: application/json' -d '{"documents":["The project codename is Nimbus-731."]}'
curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"question":"What is the project codename?","top_k":1}'
```

Windows PowerShell 请使用 `curl.exe` 或 `Invoke-RestMethod`，避免旧版 PowerShell 的 `curl` 别名差异。

## 容器与验证

```bash
docker compose -f docker-compose.integration.yml up -d --build --wait --wait-timeout 300
python -m pip install pytest httpx
python -m pytest integration_tests -q
docker compose -f docker-compose.integration.yml down
```

这个 Compose 配置验证检索和服务通信，不包含 Ollama 容器。真实生成需要另外配置可访问的 Ollama 服务。

分别在 `shared`、`service-api`、`service-rag` 中执行 `poetry run pytest -q`。生成调用在单元测试中替换为测试响应；嵌入与向量检索使用真实 MiniLM 模型。GitHub Actions 检查三个子项目及 Docker 集成流程。`.teamcity` 是另一套配置示例，其部署状态不能由 GitHub Actions 结果证明。

## 当前边界

这是工程演示项目，不是已部署的企业平台。向量库驻留内存，重启丢失，尚未提供认证、租户隔离、持久化及并发写入保护。LCEL 的上下文判断仍由模型完成，不能保证“零幻觉”。现有测试验证行为，不等于检索质量基准或真实模型回答质量评测。

`portfolio/` 保留历史实验，不属于主服务的启动与验收范围。

Windows 原生环境中，当前 FAISS/PyTorch wheel 组合会出现 OpenMP 运行库冲突并终止进程。请使用 Linux 容器或 WSL2；本项目不设置 `KMP_DUPLICATE_LIB_OK` 来绕过冲突。
