import json
import logging
import urllib.error
import urllib.request


logger = logging.getLogger("VibeOps.OllamaClient")


class OllamaClient:
    """
    Minimal HTTP client for local Ollama.

    Notes:
    - Kept dependency-free (urllib only) so it's easy to copy into interview demos.
    - Default timeout is intentionally conservative to avoid “stuck” demos.
    """

    def __init__(self, host: str = "http://localhost:11434", model: str = "gemma:4b", timeout_s: float = 60.0):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def prompt(self, system_prompt: str, user_prompt: str) -> str:
        endpoint = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,  # low temp for code/documentation tasks
                "top_p": 0.9,
            },
        }

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                result = json.loads(response.read().decode("utf-8"))
                return str(result.get("response", ""))
        except urllib.error.URLError as e:
            logger.error("Failed to connect to Ollama at %s: %s", self.host, e)
            raise RuntimeError(f"Ollama connection failed: {e}") from e
