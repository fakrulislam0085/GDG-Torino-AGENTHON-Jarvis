"""Every model call goes through this file: Gemini on Vertex AI, or an offline fallback.

Mode:
- "gemini": Vertex AI credentials found (GOOGLE_API_KEY with Vertex, or Application Default Credentials).
- "offline": no credentials, or BRAIN_MODE=offline. Callers then use their deterministic fallback.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "token-mafia-agenthon")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Running token count, so the pitch can quote a real cost per brief.
USAGE = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


class LLMUnavailable(Exception):
    """Raised when the model can't be reached or returns unusable output."""


def _adc_exists() -> bool:
    candidates = [
        Path(os.getenv("APPDATA", "")) / "gcloud" / "application_default_credentials.json",
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json",
    ]
    return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) or any(p.exists() for p in candidates)


def mode() -> str:
    if os.getenv("BRAIN_MODE", "").lower() == "offline":
        return "offline"
    if os.getenv("GOOGLE_API_KEY") or _adc_exists():
        return "gemini"
    return "offline"


_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai

        key = os.getenv("GOOGLE_API_KEY")
        if key:
            _client = genai.Client(vertexai=True, api_key=key)
        else:
            _client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    return _client


def generate_json(system: str, prompt: str, temperature: float = 0.2) -> dict:
    """Ask Gemini for a JSON object. Retries once on bad JSON. Raises LLMUnavailable."""
    if mode() != "gemini":
        raise LLMUnavailable("offline mode")
    from google.genai import types

    last_error = None
    for attempt in range(2):
        try:
            resp = _get_client().models.generate_content(
                model=MODEL,
                contents=prompt if attempt == 0 else prompt + "\n\nReturn ONLY valid JSON, nothing else.",
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
            meta = getattr(resp, "usage_metadata", None)
            USAGE["calls"] += 1
            if meta:
                USAGE["input_tokens"] += meta.prompt_token_count or 0
                USAGE["output_tokens"] += (meta.candidates_token_count or 0) + (getattr(meta, "thoughts_token_count", 0) or 0)
            data = json.loads(resp.text)
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            continue
        except Exception as e:  # network, auth, quota: never crash the demo
            raise LLMUnavailable(str(e)) from e
    raise LLMUnavailable(f"bad JSON twice: {last_error}")


def cost_eur_estimate() -> float:
    """Gemini 3.8 Flash list price from the event portal: $0.75 / 1M in, $3.75 / 1M out (USD, rough)."""
    return USAGE["input_tokens"] * 0.75 / 1e6 + USAGE["output_tokens"] * 3.75 / 1e6
