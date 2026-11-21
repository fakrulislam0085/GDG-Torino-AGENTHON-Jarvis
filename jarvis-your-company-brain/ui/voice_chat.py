"""The "Talk to Jarvis" voice mode: a live ElevenLabs voice chat shown in a dialog on the Today page.

The signed URL (short-lived) and the dynamic variables come from brain.phone.web_session. The browser SDK starts the
session only on a click inside the component, because browsers need a user gesture for the microphone.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit.components.v1 as components

_TEMPLATE = Path(__file__).with_name("voice_chat.html")


def voice_chat(signed_url: str, dynamic_variables: dict, height: int = 462) -> None:
    cfg = json.dumps({"signedUrl": signed_url, "dynamicVariables": dynamic_variables}).replace("</", "<\\/")
    components.html(_TEMPLATE.read_text(encoding="utf-8").replace("__CFG__", cfg), height=height)
