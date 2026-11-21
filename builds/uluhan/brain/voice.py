"""ElevenLabs voice brief: the morning brief read aloud (check 7, "fits the team's day").

Only the text of the brief the person may already see is sent. Audio is cached per brief run, so replaying it
costs no extra credits. Uses the low-cost Flash model. Needs ELEVENLABS_API_KEY (in .env, never in code).
"""
from __future__ import annotations

import os

import httpx

API = "https://api.elevenlabs.io/v1"
MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")
_cache: dict[str, bytes] = {}
_voice_id: str | None = None


def enabled() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY"))


def script(person: dict, brief: dict) -> str:
    first = person["name"].split()[0]
    items = brief.get("items", [])[:3]
    if not items:
        return f"Good morning {first}. Nothing needs you today."
    words = ["One", "Two", "Three"]
    parts = [f"Good morning {first}. {len(items)} thing{'s' if len(items) > 1 else ''} need you today."]
    for w, it in zip(words, items):
        parts.append(f"{w}: {it['headline'].rstrip('.')}.")
    if any(it.get("proposal_id") for it in items):
        parts.append("I've drafted a reply. It waits for your approval.")
    return " ".join(parts)[:700]


def _pick_voice(client: httpx.Client, key: str) -> str:
    global _voice_id
    if os.getenv("ELEVENLABS_VOICE_ID"):
        return os.environ["ELEVENLABS_VOICE_ID"]
    if _voice_id:
        return _voice_id
    r = client.get(f"{API}/voices", headers={"xi-api-key": key})
    r.raise_for_status()
    voices = r.json().get("voices", [])
    if not voices:
        raise RuntimeError("no voices available on this ElevenLabs account")
    _voice_id = voices[0]["voice_id"]
    return _voice_id


def speak(cache_key: str, text: str) -> bytes:
    if cache_key in _cache:
        return _cache[cache_key]
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    with httpx.Client(timeout=20) as client:
        voice = _pick_voice(client, key)
        r = client.post(f"{API}/text-to-speech/{voice}", params={"output_format": "mp3_44100_64"},
                        headers={"xi-api-key": key, "Content-Type": "application/json"},
                        json={"text": text, "model_id": MODEL})
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
        _cache[cache_key] = r.content
        return r.content
