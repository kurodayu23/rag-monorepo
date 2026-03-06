# Build from monorepo root: docker build -f service-api/Dockerfile .
# Stage 1: builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install poetry==1.8.3 --quiet
# Copy shared library first
COPY shared/ /shared/
# Copy service dependencies
COPY service-api/pyproject.toml service-api/poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && pip install faiss-cpu numpy fastapi uvicorn[standard] httpx --quiet

# Stage 2: runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY shared/ ./shared/
COPY service-api/app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
