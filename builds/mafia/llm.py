"""Gemini on Vertex AI over plain HTTPS: no SDK, nothing to install.

`generate_json(system, prompt)` returns `(dict | None, info)`. It never raises: on any problem it
returns None and the caller falls back to plain code, and the trace says so.

Auth, first match wins (see README):
  1. GOOGLE_API_KEY            Vertex AI API key (express mode)
  2. GOOGLE_ACCESS_TOKEN       e.g. the output of `gcloud auth print-access-token`
  3. Application Default Credentials file (after `gcloud auth application-default login`)
  4. the gcloud CLI, if it is on PATH
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

PRICE_IN, PRICE_OUT = 0.75 / 1e6, 3.75 / 1e6  # USD per token, gemini-3.8-flash (event brief)

_token = {"value": None, "exp": 0.0}
state = {"last_error": None, "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}

# Circuit breaker: after 2 failed calls in a row, skip Gemini for PAUSE_S seconds and answer from plain rules
# immediately (instead of making every question wait for a timeout while the Wi-Fi is down).
TIMEOUT_S = int(os.getenv("GEMINI_TIMEOUT_S", "15"))
PAUSE_S = 15
_breaker = {"fails": 0, "down_until": 0.0}


def paused() -> bool:
    return time.time() < _breaker["down_until"]


def reset_breaker():
    _breaker.update(fails=0, down_until=0.0)


def model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _adc_file() -> Path | None:
    env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    candidates = [Path(env)] if env else []
    if os.getenv("APPDATA"):
        candidates.append(Path(os.environ["APPDATA"]) / "gcloud" / "application_default_credentials.json")
    candidates.append(Path.home() / ".config" / "gcloud" / "application_default_credentials.json")
    for p in candidates:
        if p.is_file():
            return p
    return None


def configured() -> bool:
    if os.getenv("BRAIN_MODE", "auto") == "offline":
        return False
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_ACCESS_TOKEN") or _adc_file() or shutil.which("gcloud"))


def _bearer() -> str | None:
    if os.getenv("GOOGLE_ACCESS_TOKEN"):
        return os.environ["GOOGLE_ACCESS_TOKEN"]
    if _token["value"] and time.time() < _token["exp"]:
        return _token["value"]
    adc = _adc_file()
    if adc:
        info = json.loads(adc.read_text(encoding="utf-8"))
        if info.get("type") == "authorized_user":
            body = json.dumps({"client_id": info["client_id"], "client_secret": info["client_secret"],
                               "refresh_token": info["refresh_token"], "grant_type": "refresh_token"}).encode()
            req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                tok = json.loads(r.read())
            _token.update(value=tok["access_token"], exp=time.time() + int(tok.get("expires_in", 3600)) - 120)
            return _token["value"]
    gcloud = shutil.which("gcloud")
    if gcloud and time.time() > _token.get("retry_after", 0):
        out = subprocess.run([gcloud, "auth", "print-access-token"], capture_output=True, text=True, timeout=30)
        if out.returncode == 0 and out.stdout.strip():
            _token.update(value=out.stdout.strip(), exp=time.time() + 3000)
            return _token["value"]
        _token["retry_after"] = time.time() + 300  # not logged in: don't slow every call down
    return None


def _request(body: dict) -> dict:
    model = model_name()
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
    else:
        token = _bearer()
        if not token:
            raise RuntimeError("no Google credentials found")
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "token-mafia-agenthon")
        # gemini-3.8-flash is NOT served in europe-west1 (404, seen live by the team); the "eu" multi-region works.
        loc = os.getenv("GOOGLE_CLOUD_LOCATION", "eu")
        host = ("aiplatform.googleapis.com" if loc == "global" else
                f"aiplatform.{loc}.rep.googleapis.com" if loc in ("eu", "us") else f"{loc}-aiplatform.googleapis.com")
        url = (f"https://{host}/v1/projects/{project}/locations/{loc}"
               f"/publishers/google/models/{model}:generateContent")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        return json.loads(r.read())


def _parse(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t[t.find("{"):]
    return json.loads(t[t.find("{"): t.rfind("}") + 1])


def generate_json(system: str, prompt: str) -> tuple[dict | None, dict]:
    info = {"mode": "gemini", "model": model_name(), "ms": 0, "input_tokens": 0, "output_tokens": 0,
            "cost_usd": 0.0, "error": None}
    if not configured():
        info.update(mode="offline", error="Gemini not configured")
        return None, info
    if paused():
        info.update(mode="offline", error=f"Gemini paused after repeated errors; using rules for "
                                          f"{int(_breaker['down_until'] - time.time())} s more")
        return None, info
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    if os.getenv("GEMINI_THINKING", "low"):  # low thinking: ~2 s per call instead of ~10 s (measured by the team)
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": os.getenv("GEMINI_THINKING", "low").upper()}
    t0 = time.time()
    for attempt in (1, 2):
        try:
            resp = _request(body)
            parts = resp["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            u = resp.get("usageMetadata", {})
            info["input_tokens"] = u.get("promptTokenCount", 0)
            info["output_tokens"] = u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
            info["cost_usd"] = round(info["input_tokens"] * PRICE_IN + info["output_tokens"] * PRICE_OUT, 6)
            info["ms"] = int((time.time() - t0) * 1000)
            state["calls"] += 1
            state["input_tokens"] += info["input_tokens"]
            state["output_tokens"] += info["output_tokens"]
            state["cost_usd"] = round(state["cost_usd"] + info["cost_usd"], 6)
            state["last_error"] = None
            _breaker["fails"] = 0
            return _parse(text), info
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
            retry = e.code in (429, 500, 502, 503, 504)
        except Exception as e:  # network, timeout, bad JSON, missing fields
            err, retry = f"{type(e).__name__}: {e}"[:300], False
        if not (retry and attempt == 1):
            break
        time.sleep(1.5)
    info.update(mode="offline", error=err, ms=int((time.time() - t0) * 1000))
    state["last_error"] = err
    # two failures in a row (timeouts included) pause Gemini briefly; one slow call alone does not
    _breaker["fails"] += 1
    if _breaker["fails"] >= 2:
        _breaker["down_until"] = time.time() + PAUSE_S
    return None, info
