## Django API 设计（代理到 service-api）

这个目录的重点是“API 层如何设计并对接后端微服务”，所以它不会在 Django 里重新实现 RAG。

- Django 提供对外入口：`/health`、`/documents`、`/query`
- Django 用 HTTP 代理请求到本 repo 的 `service-api`（默认 `http://localhost:8000`）

### 运行示例

```bash
cd portfolio/django_api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

set RAG_SERVICE_API_BASE_URL=http://localhost:8000
python manage.py runserver 0.0.0.0:8002
```

### API 对外接口

- `GET /health`
- `POST /documents`
  - body: `{ "documents": ["..."] }`
- `POST /query`
  - body: `{ "question": "...", "top_k": 3 }`

### 面试讲解要点

- Django 负责“入口形态”和“请求/响应契约”
- 下游的 RAG 逻辑放在 `service-api` / `service-rag`，便于扩展与单测

