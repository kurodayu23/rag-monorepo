from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def _get_upstream_base_url() -> str:
    # Where Django proxies requests to (this repo's FastAPI gateway).
    return os.environ.get("RAG_SERVICE_API_BASE_URL", "http://localhost:8000").rstrip("/")


def _proxy_post(endpoint: str, body: Dict[str, Any]) -> JsonResponse:
    url = f"{_get_upstream_base_url()}{endpoint}"
    resp = requests.post(url, json=body, timeout=20.0)
    try:
        payload = resp.json()
    except Exception:
        payload = {"error": f"Upstream returned non-JSON (status={resp.status_code})"}
    return JsonResponse(payload, status=resp.status_code, safe=isinstance(payload, dict))


@require_http_methods(["GET"])
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "upstream": _get_upstream_base_url()})


@csrf_exempt
@require_http_methods(["POST"])
def documents(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body.decode("utf-8") or "{}")
    if "documents" not in body:
        return JsonResponse({"error": "Missing 'documents' field"}, status=400)
    return _proxy_post("/documents", body)


@csrf_exempt
@require_http_methods(["POST"])
def query(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body.decode("utf-8") or "{}")
    if "question" not in body:
        return JsonResponse({"error": "Missing 'question' field"}, status=400)
    return _proxy_post("/query", body)

