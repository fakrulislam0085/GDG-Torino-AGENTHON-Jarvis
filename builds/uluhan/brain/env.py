"""Load KEY=VALUE lines from .env files into os.environ (without overriding what is already set).

Looked up in builds/uluhan/.env, then the repo root .env. Both are git-ignored. Never commit keys.
"""
from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # builds/uluhan
CANDIDATES = [HERE / ".env", HERE.parent.parent / ".env"]


def load() -> list[str]:
    loaded = []
    for path in CANDIDATES:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v
        loaded.append(str(path))
    return loaded
