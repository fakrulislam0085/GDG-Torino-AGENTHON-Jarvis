"""Offline tests for "Talk to Jarvis" (phone.web_session). The ElevenLabs HTTP is mocked: no real network.
Run from jarvis-your-company-brain: python -m pytest tests -q"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["BRAIN_MODE"] = "offline"
os.environ["JARVIS_DATA"] = "data_filare"
os.environ.setdefault("BRAIN_STATE_DIR", tempfile.mkdtemp(prefix="brain-best-voice-"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from brain import brief, llm, phone, store  # noqa: E402


class _Resp:
    def __init__(self, status, payload):
        self.status_code, self._p = status, payload

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    store.reset_demo()
    llm.reset_breaker()
    brief.sweep()
    monkeypatch.setattr(phone, "_web_agent_id", None)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    seen = {"get": [], "post": [], "patch": []}

    def get(url, **k):
        seen["get"].append(url)
        if "get-signed-url" in url:
            return _Resp(200, {"signed_url": "wss://example.test/signed"})
        return _Resp(200, {"agents": [{"name": phone.WEB_AGENT_NAME, "agent_id": "agent-web"}]})

    def patch(url, **k):
        seen["patch"].append((url, k.get("json")))
        return _Resp(200, {})

    def post(url, **k):  # creating agents or placing calls must never happen here
        seen["post"].append(url)
        raise AssertionError("no POST expected")

    monkeypatch.setattr(phone.requests, "get", get)
    monkeypatch.setattr(phone.requests, "patch", patch)
    monkeypatch.setattr(phone.requests, "post", post)
    yield seen


def _finance_only():
    return [m for m in store.memory() if set(m.get("acl", [])) == {"finance"}]


def test_web_session_returns_signed_url_and_uses_the_web_agent_not_the_phone_agent(fresh):
    out = phone.web_session(store.ceo())
    assert out["ok"] and out["signed_url"] == "wss://example.test/signed"
    assert any("agent-web" in str(k) or "get-signed-url" in u for u in fresh["get"] for k in [u])
    patched = fresh["patch"][0][1]["conversation_config"]["agent"]
    assert patched["prompt"]["prompt"] == phone.WEB_PROMPT and "urgent came in" not in patched["prompt"]["prompt"]
    assert not fresh["post"]                                    # no call placed, nothing created
    assert set(out["dynamic_variables"]) == {"company", "name", "brief", "team", "audiences", "memory"}
    rows = [r for r in (store.STATE / "audit.jsonl").read_text(encoding="utf-8").splitlines() if "voice_chat_started" in r]
    assert rows and "signed" not in rows[-1]                     # audit: user only, no URL, no content


def test_finance_only_facts_never_reach_the_voice_agent():
    fin = _finance_only()
    assert fin
    fin_ids = {m["id"] for m in fin}
    held = 0
    for user in store.people():                                  # every role, the CEO and finance included
        dyn = phone.web_session(user)["dynamic_variables"]
        blob = " ".join(str(v) for v in dyn.values()).lower()
        for m in fin:
            assert m["fact"].lower()[:50] not in blob
        b = store.briefs()[user]
        for it in b.get("alerts", []) + b["items"]:
            if set(it.get("cited", [])) & fin_ids:
                held += 1
                assert it["text"].lower()[:50] not in blob         # brief items built on finance-only facts are held back
    assert held                                                   # the data really has such items, so the check bites


def test_only_the_requesting_users_brief_is_used():
    briefs = store.briefs()
    me = next(u for u in store.people() if u != store.ceo())
    dyn = phone.web_session(me)["dynamic_variables"]
    mine = [i["text"] for i in briefs[me]["items"]]
    assert any(t[:50] in dyn["brief"] for t in mine)
    for other, b in briefs.items():
        if other == me:
            continue
        for it in b["items"]:
            if it["text"] not in mine:
                assert it["text"][:50] not in dyn["brief"]
    assert dyn["name"] == store.people()[me]["name"].split()[0]


def test_fails_gracefully_when_not_configured(monkeypatch, fresh):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    out = phone.web_session(store.ceo())
    assert out == {"ok": False, "message": phone.UNAVAILABLE}
    assert not fresh["get"] and not fresh["patch"]               # no network at all


def test_fails_gracefully_when_elevenlabs_errors(monkeypatch):
    monkeypatch.setattr(phone.requests, "get", lambda url, **k: _Resp(401, {"detail": "bad key"}))
    assert phone.web_session(store.ceo()) == {"ok": False, "message": phone.UNAVAILABLE}

    def boom(url, **k):
        raise ConnectionError("network down")
    monkeypatch.setattr(phone.requests, "get", boom)
    assert phone.web_session(store.ceo()) == {"ok": False, "message": phone.UNAVAILABLE}
    assert phone.web_session("nobody")["ok"] is False             # unknown user: no session


def test_phone_agent_defaults_unchanged(fresh, monkeypatch):
    monkeypatch.setattr(phone.requests, "get", lambda url, **k: _Resp(200, {"agents": [{"name": phone.AGENT_NAME, "agent_id": "agent-phone"}]}))
    assert phone.ensure_agent() == "agent-phone"
    cfg = fresh["patch"][-1][1]["conversation_config"]["agent"]
    assert cfg["prompt"]["prompt"] == phone.PROMPT and cfg["first_message"] == phone.FIRST_MESSAGE

