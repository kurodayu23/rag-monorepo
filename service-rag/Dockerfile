# Build from monorepo root: docker build -f service-rag/Dockerfile .
# Stage 1: builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install poetry==1.8.3 --quiet
# Copy shared library
COPY shared/ /shared/
# Copy service dependencies
COPY service-rag/pyproject.toml service-rag/poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && pip install faiss-cpu numpy ollama --quiet

# Stage 2: runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY shared/ ./shared/
COPY service-rag/app/ ./app/
EXPOSE 8001
ENV OLLAMA_MODEL=llama3
CMD ["python", "-m", "app.main"]
