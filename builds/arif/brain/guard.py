"""Defences against rivals: injection detection and wrapping source text as data."""
from __future__ import annotations

import re

_PATTERNS = [
    (r"ignore (all |any )?(your |the )?(previous |prior |earlier )?(rules|instructions)", "tells the assistant to ignore its rules"),
    (r"\badmin mode\b|\bdeveloper mode\b|\bjailbreak\b", "claims a special mode"),
    (r"(do not|don't|without) ask(ing)? (anyone |a person )?(for )?approval", "tries to skip approval"),
    (r"\b(ai|assistant|brain)\b[^.\n]{0,30}\b(reading this|you are now)\b", "speaks directly to the AI"),
    (r"\bforward\b[^.\n]{0,80}\b[\w.+-]+@[\w-]+\.[\w.]+", "asks to forward data to an address"),
    (r"\b(salary|salaries|bank balance|iban|password)\b[^.\n]{0,60}\b(send|forward|share|email)\b|\b(send|forward|share|email)\b[^.\n]{0,60}\b(salary|salaries|bank balance|password)\b", "asks for sensitive data"),
]


def suspicious(text: str) -> list:
    """Reasons this text looks like an attack on the assistant (empty list = looks fine)."""
    t = text.lower()
    return [why for pat, why in _PATTERNS if re.search(pat, t)]


def as_data(item_id: str, text: str) -> str:
    """Source text goes to the model fenced as data. The system prompt says data is never instructions."""
    clean = text.replace("<<", "«").replace(">>", "»")
    return f"<<DATA id={item_id}>>\n{clean}\n<<END DATA>>"
