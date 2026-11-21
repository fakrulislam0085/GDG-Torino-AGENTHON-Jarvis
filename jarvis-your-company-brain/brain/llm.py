"""Every model call goes through this file: Gemini on Vertex AI, or an offline fallback.

Mode:
- "gemini": Vertex AI credentials found (GOOGLE_API_KEY with Vertex, or Application Default Credentials).
- "offline": no credentials, or BRAIN_MODE=offline. Callers then use their deterministic fallback.

Circuit breaker: after 2 consecutive failed calls, Gemini is skipped for 60 s (every call raises LLMUnavailable at
once and mode() says "offline"), so a dead network never makes each click wait for a timeout. Then it tries again.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "token-mafia-agenthon")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Running token count, so the pitch can quote a real cost per brief.
USAGE = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


class LLMUnavailable(Exception):
    """Raised when the model can't be reached or returns unusable output."""


# ---------- circuit breaker ----------
BREAKER_FAILS = 2        # consecutive failures that open the breaker
BREAKER_SECONDS = 60     # how long Gemini is skipped once open
_BREAKER = {"fails": 0, "open_until": 0.0}
_BREAKER_LOCK = threading.Lock()


def breaker_remaining() -> int:
    """Seconds left while Gemini is paused after repeated failures (0 = closed, calls go through)."""
    with _BREAKER_LOCK:
        return max(0, int(round(_BREAKER["open_until"] - time.monotonic())))


def _record(ok: bool) -> None:
    with _BREAKER_LOCK:
        if ok:
            _BREAKER["fails"] = 0
            _BREAKER["open_until"] = 0.0
            return
        _BREAKER["fails"] += 1
        if _BREAKER["fails"] >= BREAKER_FAILS:
            _BREAKER["open_until"] = time.monotonic() + BREAKER_SECONDS


def reset_breaker() -> None:
    with _BREAKER_LOCK:
        _BREAKER.update(fails=0, open_until=0.0)


def _adc_exists() -> bool:
    candidates = [
        Path(os.getenv("APPDATA", "")) / "gcloud" / "application_default_credentials.json",
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json",
    ]
    return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) or any(p.exists() for p in candidates)


def configured_mode() -> str:
    """What the credentials allow, ignoring the breaker."""
    if os.getenv("BRAIN_MODE", "").lower() == "offline":
        return "offline"
    if os.getenv("GOOGLE_API_KEY") or _adc_exists():
        return "gemini"
    return "offline"


def mode() -> str:
    """'gemini' or 'offline'. Offline too while the breaker is open, so callers go straight to their fallback."""
    m = configured_mode()
    if m == "gemini" and breaker_remaining() > 0:
        return "offline"
    return m


_local = threading.local()  # one client per thread: briefs run in parallel


def _get_client():
    client = getattr(_local, "client", None)
    if client is None:
        from google import genai
        from google.genai import types as _t

        _http = _t.HttpOptions(timeout=20000)  # ms: a dead Wi-Fi must not hang a click
        key = os.getenv("GOOGLE_API_KEY")
        if key:
            client = genai.Client(vertexai=True, api_key=key, http_options=_http)
        else:
            client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION, http_options=_http)
        _local.client = client
    return client


def generate_json(system: str, prompt: str, temperature: float = 0.2) -> dict:
    """Ask Gemini for a JSON object. Retries once on bad JSON. Raises LLMUnavailable."""
    if configured_mode() != "gemini":
        raise LLMUnavailable("offline mode")
    if breaker_remaining() > 0:
        raise LLMUnavailable(f"Gemini paused for {breaker_remaining()} s after {BREAKER_FAILS} failures in a row")
    try:
        out = _generate(system, prompt, temperature)
    except LLMUnavailable:
        _record(False)
        raise
    _record(True)
    return out


def _generate(system: str, prompt: str, temperature: float) -> dict:
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
                    # Low thinking: measured 2.1 s per call instead of 9.7 s, same JSON quality for these short tasks.
                    thinking_config=types.ThinkingConfig(thinking_level=os.getenv("GEMINI_THINKING", "low")),
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
