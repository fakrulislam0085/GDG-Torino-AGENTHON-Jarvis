"""Optional ElevenLabs voice for the morning brief (text to speech over plain HTTPS, no SDK).

Set ELEVENLABS_API_KEY (in a git-ignored .env) to turn it on. Without a key the page falls back to the
browser's own voice. ELEVENLABS_VOICE_ID picks a voice (default: the first voice on the account) and
ELEVENLABS_MODEL the model (default eleven_flash_v2_5, the cheapest). Only the text of the signed-in
person's own brief is ever sent.
"""
from __future__ import annotations

import json
import os
import urllib.request

_voice = {"id": None}


def configured() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY"))


def _headers() -> dict:
    return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}


def voice_id() -> str:
    if os.getenv("ELEVENLABS_VOICE_ID"):
        return os.environ["ELEVENLABS_VOICE_ID"]
    if not _voice["id"]:
        req = urllib.request.Request("https://api.elevenlabs.io/v1/voices", headers=_headers())
        with urllib.request.urlopen(req, timeout=6) as r:
            _voice["id"] = json.load(r)["voices"][0]["voice_id"]
    return _voice["id"]


def speak(text: str) -> bytes:
    body = json.dumps({"text": text[:2500], "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id()}?output_format=mp3_44100_64", data=body,
        headers={**_headers(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()
