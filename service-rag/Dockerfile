# 从仓库根目录构建。
FROM python:3.11-slim
RUN pip install --no-cache-dir poetry==1.8.3
WORKDIR /workspace
COPY shared/ ./shared/
COPY service-rag/ ./service-rag/
WORKDIR /workspace/service-rag
RUN poetry config virtualenvs.create false && poetry install --only main --extras langchain_engine --no-interaction
EXPOSE 8001
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
