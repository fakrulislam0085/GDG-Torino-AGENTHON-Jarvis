"""The morning brief, read aloud with ElevenLabs (only if ELEVENLABS_API_KEY is set in builds/best/.env).
Only the text the person already sees is sent (their role-filtered brief or call script). The audio cache is keyed by a
hash of that text, so a changed brief is never read out from an old recording."""
from __future__ import annotations

import hashlib
import os

import requests
from dotenv import load_dotenv

from . import store

load_dotenv(store.BUILD / ".env")


def available() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY"))


def speak(user_id: str, text: str) -> bytes:
    digest = hashlib.sha256(text[:2500].encode("utf-8")).hexdigest()[:16]
    cache = store.STATE / f"voice-{user_id}-{digest}.mp3"
    if cache.exists():
        return cache.read_bytes()
    voice = os.getenv("ELEVENLABS_VOICE_ID", "onwK4e9ZLuTAKqWW03F9")
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
