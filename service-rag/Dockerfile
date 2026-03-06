# ── Stage 1: builder ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock* ./
COPY ../shared /shared
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction

# ── Stage 2: runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/
EXPOSE 8001
ENV OLLAMA_MODEL=llama3
CMD ["python", "-c", "from app.main import query; print(query('What is RAG?'))"]
