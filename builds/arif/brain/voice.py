"""The morning brief, read aloud with ElevenLabs (only if ELEVENLABS_API_KEY is set in builds/ari/.env)."""
from __future__ import annotations

import os

import requests

from . import store


def available() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY"))


def speak(user_id: str, text: str) -> bytes:
    cache = store.STATE / f"voice-{user_id}.mp3"
    if cache.exists():
        return cache.read_bytes()
    voice = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "accept": "audio/mpeg"},
        json={"text": text[:2500], "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")},
        timeout=40,
    )
    r.raise_for_status()
    store.STATE.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(r.content)
    return r.content
