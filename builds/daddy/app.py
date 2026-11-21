"""Filare Brain web server. Standard library only.

    python builds/daddy/app.py          ->  http://localhost:8020

Reads Gemini settings from the environment or a git-ignored .env (see README). Without them it runs
the offline rules and says so on screen. State (decisions, drafts, log) is saved to a git-ignored
state.json, so a restart loses nothing; "Reset demo" wipes it.
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

PERSIST = os.getenv("BRAIN_PERSIST", "on") != "off"
BRAIN = B.Brain(persist=PERSIST)
SWEEP_EVERY = int(os.getenv("SWEEP_EVERY_MIN", "30")) * 60


class Handler(BaseHTTPRequestHandler):
    brain = BRAIN
    allowed_hosts: set[str] = set()  # "localhost:8020", "127.0.0.1:8020"; filled in by make_server()

    def log_message(self, *a):  # keep the console quiet
        pass

    def _send(self, code, obj=None, body=None, ctype="application/json"):
        data = body if body is not None else json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _allowed(self, post: bool) -> bool:
        """Only the page we serve may call the API. Without this, any website open in the same browser could
        send a request to localhost and approve an action as someone else (CSRF), or read data (DNS rebinding)."""
        if self.headers.get("Host", "") not in self.allowed_hosts:
            self._send(403, {"error": "unexpected Host header"})
            return False
        origin = self.headers.get("Origin")
        if origin and origin.split("://", 1)[-1] not in self.allowed_hosts:
            self._send(403, {"error": "cross-origin request refused"})
            return False
        if post and not (self.headers.get("Content-Type", "").lower().startswith("application/json")):
            self._send(415, {"error": "Content-Type must be application/json"})
            return False
        return True

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
        if not self._allowed(False):
            return
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in ("/", "/index.html"):
            return self._send(200, body=(HERE / "web" / "index.html").read_bytes(), ctype="text/html")
        if u.path == "/api/state":
            return self._run(lambda: self.brain.view(q.get("user", "")))
        if u.path == "/api/source":
            return self._run(lambda: self.brain.open_source(q.get("user", ""), q.get("id", "")))
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._allowed(True):
            return
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        if n > 20_000:
            return self._send(413, {"error": "request too large"})
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            assert isinstance(body, dict)
        except (json.JSONDecodeError, AssertionError):
            return self._send(400, {"error": "bad JSON"})
        user, brain = body.get("user", ""), self.brain
        if user not in brain.people:
            return self._send(403, {"error": "unknown user"})
        routes = {
            "/api/ask": lambda: brain.ask(user, body.get("question", "")),
            "/api/memory": lambda: brain.review_memory(user, body.get("id", ""), body.get("decision", ""),
                                                       body.get("reason", "")),
            "/api/action": lambda: brain.decide_action(user, body.get("id", ""), body.get("decision", ""),
                                                       body.get("body"), body.get("reason", "")),
            "/api/sweep": lambda: (threading.Thread(target=brain.sweep, args=(user,), daemon=True).start(),
                                   {"ok": True})[1],
            "/api/simulate": lambda: brain.ingest(body.get("id", ""), actor=f"mail (sent by {user} for the demo)"),
            "/api/inbound": lambda: brain.receive_email(user, body.get("from", ""), body.get("subject", ""),
                                                        body.get("body", "")),
            "/api/reset": lambda: (brain.reset(actor=user), start_sweep(brain), {"ok": True})[2],
        }
        if u.path not in routes:
            return self._send(404, {"error": "not found"})
        self._run(routes[u.path])


def start_sweep(brain=None):
    threading.Thread(target=(brain or BRAIN).sweep, daemon=True).start()


def scheduler():
    """Speaks first: the morning sweep runs on its own at start-up, then on a timer. A brief is only posted
    when something changed, so the timer never repeats itself."""
    start_sweep()
    while SWEEP_EVERY > 0:
        time.sleep(SWEEP_EVERY)
        BRAIN.sweep("schedule")


def make_server(port: int, brain=None) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"brain": brain or BRAIN,
                                                "allowed_hosts": {f"localhost:{port}", f"127.0.0.1:{port}"}})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main():
    port = int(os.getenv("PORT", "8020"))
    threading.Thread(target=scheduler, daemon=True).start()
    print(f"Filare Brain on http://localhost:{port}  (mode: {BRAIN.mode()}, state saved: {PERSIST})")
    make_server(port).serve_forever()


if __name__ == "__main__":
    main()
