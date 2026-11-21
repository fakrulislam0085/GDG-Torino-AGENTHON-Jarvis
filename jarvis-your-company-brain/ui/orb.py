"""The Jarvis orb: one three.js component (idle in the Today header, speaking in the call card and for "Play my brief").

Rendered with streamlit.components.v1.html. Falls back to a static SVG orb when WebGL is missing, the viewport is
under 768px, or the viewer prefers reduced motion. Audio is embedded as base64 and played inside the iframe through
a WebAudio AnalyserNode that drives the orb's scale and glow.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import streamlit.components.v1 as components

_TEMPLATE = Path(__file__).with_name("orb.html")
CONTROLS_H = 58  # Play button row under a speaking orb


def orb(size: int = 140, *, audio: bytes | None = None, nonce: str = "", autoplay: bool = False) -> None:
    """Idle orb when audio is None; speaking orb with an in-iframe Play control otherwise.
    nonce + autoplay: try to speak once for this nonce (a call id or a brief request), never again on reruns."""
    cfg = {
        "size": size,
        "big": audio is not None,
        "audio": base64.b64encode(audio).decode("ascii") if audio else "",
        "nonce": nonce,
        "autoplay": bool(autoplay and audio),
    }
    page = _TEMPLATE.read_text(encoding="utf-8").replace("__SIZE__", str(size)).replace("__CFG__", json.dumps(cfg))
    components.html(page, height=size + (CONTROLS_H if audio else 0))

