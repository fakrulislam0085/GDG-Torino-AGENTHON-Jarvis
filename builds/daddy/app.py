"""Filare Brain web server. Standard library only.

    python builds/daddy/app.py          ->  http://localhost:8020

Reads Gemini settings from the environment or a git-ignored .env (see README). Without them it runs
the offline rules and says so on screen.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent


def load_env():
    for env in (HERE / ".env", HERE.parent.parent / ".env"):
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
sys.path.insert(0, str(HERE))
import brain as B  # noqa: E402

BRAIN = B.Brain()
SWEEP_EVERY = int(os.getenv("SWEEP_EVERY_MIN", "30")) * 60


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # keep the console quiet
        pass

    def _send(self, code, obj=None, body=None, ctype="application/json"):
        data = body if body is not None else json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _run(self, fn):
        try:
            self._send(200, fn())
        except PermissionError as e:
            self._send(403, {"error": str(e)})
        except KeyError as e:
            self._send(404, {"error": f"not found: {e}"})
        except ValueError as e:
            self._send(400, {"error": str(e)})

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in ("/", "/index.html"):
            return self._send(200, body=(HERE / "web" / "index.html").read_bytes(), ctype="text/html")
        if u.path == "/api/state":
            return self._run(lambda: BRAIN.view(q.get("user", "")))
        if u.path == "/api/source":
            return self._run(lambda: BRAIN.open_source(q.get("user", ""), q.get("id", "")))
        self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "bad JSON"})
        user = body.get("user", "")
        if u.path != "/api/reset" and user not in BRAIN.people:
            return self._send(403, {"error": "unknown user"})
        routes = {
            "/api/ask": lambda: BRAIN.ask(user, body.get("question", "")),
            "/api/memory": lambda: BRAIN.review_memory(user, body.get("id", ""), body.get("decision", ""),
                                                       body.get("reason", "")),
            "/api/action": lambda: BRAIN.decide_action(user, body.get("id", ""), body.get("decision", ""),
                                                       body.get("body"), body.get("reason", "")),
            "/api/sweep": lambda: (threading.Thread(target=BRAIN.sweep, args=(user,), daemon=True).start(),
                                   {"ok": True})[1],
            "/api/simulate": lambda: BRAIN.ingest(body.get("id", ""), actor=f"mail (sent by {user} for the demo)"),
            "/api/reset": lambda: (BRAIN.reset(actor=user or "system"), start_sweep(), {"ok": True})[2],
        }
        if u.path not in routes:
            return self._send(404, {"error": "not found"})
        self._run(routes[u.path])


def start_sweep():
    threading.Thread(target=BRAIN.sweep, daemon=True).start()


def scheduler():
    """Speaks first: the morning sweep runs on its own at start-up, then on a timer."""
    start_sweep()
    while SWEEP_EVERY > 0:
        time.sleep(SWEEP_EVERY)
        BRAIN.sweep("schedule")


def main():
    port = int(os.getenv("PORT", "8020"))
    threading.Thread(target=scheduler, daemon=True).start()
    print(f"Filare Brain on http://localhost:{port}  (mode: {BRAIN.mode()})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
