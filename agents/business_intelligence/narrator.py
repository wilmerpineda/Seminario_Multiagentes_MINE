from __future__ import annotations

import json
import os
import urllib.request


def _post(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def enrich_summary(question: str, deterministic_summary: str, rows: list[dict]) -> str:
    """Optionally rewrite a verified summary; failure never blocks analytics."""
    if os.getenv("ENABLE_LLM", "false").lower() != "true":
        return deterministic_summary
    prompt = f"Reescribe en español ejecutivo sin agregar cifras ni causalidad. Pregunta: {question}\nResumen verificado: {deterministic_summary}\nMuestra: {json.dumps(rows[:10], default=str)}"
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        result = _post(f"{host}/api/generate", {"model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"), "prompt": prompt, "stream": False})
        return result["response"].strip()
    if provider == "vertex":
        import google.auth
        from google.auth.transport.requests import Request

        credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(Request())
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        model = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
        project = os.getenv("GOOGLE_CLOUD_PROJECT", project)
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent"
        result = _post(url, {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1}}, {"Authorization": f"Bearer {credentials.token}"})
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    raise ValueError(f"Proveedor LLM no soportado: {provider}")
