"""Append-only log of everything Jarvis does: who, what, on which input, who approved."""
from __future__ import annotations

import json
import threading
from datetime import datetime

from . import store


def _path():
    return store.STATE / "audit.jsonl"


_LOCK = threading.Lock()


def log(event: str, user_id: str | None = None, **details) -> dict:
    row = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, "user": user_id, **details}
    with _LOCK:
        store.STATE.mkdir(parents=True, exist_ok=True)
        with _path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read() -> list:
    try:
        return [json.loads(line) for line in _path().read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError:
        return []
