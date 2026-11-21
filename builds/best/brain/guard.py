"""Defences against rivals: injection detection and wrapping source text as data."""
from __future__ import annotations

import re
import unicodedata

_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad"), None)
_LOOKALIKE = str.maketrans("\u0430\u0435\u043e\u0440\u0441\u0443\u0445\u0456\u0458\u0455\u0501\u0261\u04bb\u0410\u0412\u0415\u041a\u041c\u041d\u041e\u0420\u0421\u0422\u0425",
                           "aeopcyxijsdghABEKMHOPCTX")


def normalise(text: str) -> str:
    """Undo common disguises before checking: full-width letters, zero-width characters, Cyrillic look-alikes."""
    return unicodedata.normalize("NFKC", text).translate(_ZERO_WIDTH).translate(_LOOKALIKE)

_PATTERNS = [
    (r"ignore (all |any )?(your |the )?(previous |prior |earlier )?(rules|instructions)", "tells the assistant to ignore its rules"),
    (r"\badmin mode\b|\bdeveloper mode\b|\bjailbreak\b", "claims a special mode"),
    (r"(do not|don't|without) ask(ing)? (anyone |a person )?(for )?approval", "tries to skip approval"),
    (r"\b(ai|assistant|brain|jarvis)\b[^.\n]{0,30}\b(reading this|you are now)\b", "speaks directly to the AI"),
    (r"\bforward\b[^.\n]{0,80}\b[\w.+-]+@[\w-]+\.[\w.]+", "asks to forward data to an address"),
    (r"(disregard|forget|override|set aside)\s+(all\s+|any\s+)?(prior|previous|earlier|your|the)\s+(guidance|instructions|rules|directions|policies)", "tells the assistant to drop its rules"),
    (r"no need to (check|ask|confirm) with anyone|without (checking|asking|telling) (with )?anyone", "tries to skip approval"),
    (r"\b(iban|bank details|bank account|wire|transfer|bonifico)\b[^\n]{0,160}\b(urgent|urgently|today|immediately|confidential|quietly|don'?t tell|do not tell|keep (this|it) between us)\b|\b(urgent|urgently|confidential|quietly|don'?t tell|do not tell|keep (this|it) between us)\b[^\n]{0,160}\b(iban|bank details|bank account|wire|transfer|bonifico)\b", "asks for an urgent or secret payment (possible CEO fraud)"),
    (r"\b(salary|salaries|bank balance|iban|password)\b[^.\n]{0,60}\b(send|forward|share|email)\b|\b(send|forward|share|email)\b[^.\n]{0,60}\b(salary|salaries|bank balance|password)\b", "asks for sensitive data"),
]


def suspicious(text: str) -> list:
    """Reasons this text looks like an attack on the assistant (empty list = looks fine)."""
    t = normalise(text).lower()
    return [why for pat, why in _PATTERNS if re.search(pat, t)]


def as_data(item_id: str, text: str) -> str:
    """Source text goes to the model fenced as data. The system prompt says data is never instructions."""
    clean = text.replace("<<", "«").replace(">>", "»")
    return f"<<DATA id={item_id}>>\n{clean}\n<<END DATA>>"
