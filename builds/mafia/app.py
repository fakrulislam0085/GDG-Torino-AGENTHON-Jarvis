"""Company Brain "mafia" web server. Standard library only.

    python builds/mafia/app.py          ->  http://localhost:8030

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
import voice  # noqa: E402

PERSIST = os.getenv("BRAIN_PERSIST", "on") != "off"
BRAIN = B.Brain(persist=PERSIST)
SWEEP_EVERY = int(os.getenv("SWEEP_EVERY_MIN", "30")) * 60


COOLDOWN_S = {"/api/ask": 1.0, "/api/sweep": 10.0, "/api/reset": 10.0, "/api/inbound": 3.0, "/api/voice": 2.0,
              "/api/call/dial": 20.0}


class Handler(BaseHTTPRequestHandler):
    timeout = 15  # a client that stops sending cannot hold a thread forever
    brain = BRAIN
    last_call: dict = {}  # (user, path) -> time of the last call: a cooldown against spam and cost
    voice_cache: dict = {}  # (user, brief id) -> mp3, so a click never pays twice
    allowed_hosts: set[str] = set()  # "localhost:8020", "127.0.0.1:8020"; filled in by make_server()

    def log_message(self, *a):  # keep the console quiet
        pass

    def _send(self, code, obj=None, body=None, ctype="application/json"):
        data = body if body is not None else json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype if ctype.startswith("audio") else ctype + "; charset=utf-8")
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
        except (ValueError, TypeError, AttributeError) as e:  # bad input of any kind: 400, never a dead connection
            self._send(400, {"error": str(e) if isinstance(e, ValueError) else "bad request"})

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
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0:
            return self._send(400, {"error": "bad Content-Length"})
        if n > 20_000:
            return self._send(413, {"error": "request too large"})
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            assert isinstance(body, dict)
        except (json.JSONDecodeError, AssertionError):
            return self._send(400, {"error": "bad JSON"})
        user, brain = body.get("user", ""), self.brain
        if not isinstance(user, str) or user not in brain.people:
            return self._send(403, {"error": "unknown user"})
        if u.path == "/api/reset" and "exec" not in brain.people[user]["groups"]:
            return self._send(403, {"error": "Only the CEO (exec) can reset the demo"})
        wait = COOLDOWN_S.get(u.path)
        now = time.time()
        if wait and now - self.last_call.get((user, u.path), 0) < wait:
            return self._send(429, {"error": "Slow down a little"})
        self.last_call[(user, u.path)] = now
        if u.path == "/api/voice":  # the brief read aloud by ElevenLabs (503 if no key: the page falls back)
            try:
                rid = body.get("id", "")
                text = brain.call_text(user, rid) if str(rid).startswith("call-") else brain.brief_text(user, rid)
                if not voice.configured():
                    return self._send(503, {"error": "ElevenLabs voice is not configured"})
                key = (user, body.get("id", ""))
                if key not in self.voice_cache:
                    self.voice_cache[key] = voice.speak(text)
                return self._send(200, body=self.voice_cache[key], ctype="audio/mpeg")
            except KeyError:
                return self._send(404, {"error": "not found"})
            except Exception as e:  # network, quota, bad key: never break the page
                return self._send(502, {"error": f"voice failed: {type(e).__name__}"})
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
            "/api/call/answer": lambda: brain.answer_call(user, body.get("id", ""), "answered"),
            "/api/call/end": lambda: brain.answer_call(user, body.get("id", ""),
                                                       "declined" if body.get("decision") == "declined" else "ended"),
            "/api/call/dial": lambda: brain.dial_real(user, body.get("id", "")),
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
    handler = type("BoundHandler", (Handler,), {"brain": brain or BRAIN, "last_call": {}, "voice_cache": {},
                                                "allowed_hosts": {f"localhost:{port}", f"127.0.0.1:{port}"}})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main():
    port = int(os.getenv("PORT", "8030"))
    threading.Thread(target=scheduler, daemon=True).start()
    print(f"Filare Brain on http://localhost:{port}  (mode: {BRAIN.mode()}, state saved: {PERSIST})")
    make_server(port).serve_forever()


if __name__ == "__main__":
    main()
