"""Offline tests for the second round of grafts (self-check, quote check, outbox privacy, timer, strict matching).
Run from jarvis-your-company-brain: ..\\arif\\.venv\\Scripts\\python -m pytest tests -q"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["BRAIN_MODE"] = "offline"
os.environ["JARVIS_DATA"] = "data_filare"          # tests always run on the Filare data, whatever .env says
os.environ.setdefault("BRAIN_STATE_DIR", tempfile.mkdtemp(prefix="brain-best-grafts-"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from brain import answer, audit, brief, llm, memory, propose, store, watch  # noqa: E402


@pytest.fixture(autouse=True)
def fresh():
    store.reset_demo()
    llm.reset_breaker()
    brief.sweep()
    yield


def gemini_returns(monkeypatch, payload):
    """Pretend Gemini is up and answers every call with `payload` (no network)."""
    monkeypatch.setattr(llm, "configured_mode", lambda: "gemini")
    monkeypatch.setattr(llm, "_generate", lambda *a, **k: payload)


# ---------- 1. draft self-check ----------
def test_self_check_offline_says_it_needs_gemini_and_never_blocks():
    a = propose.for_user("luca")[0]
    assert propose.self_check(a["id"], "luca") == {"status": "offline", "items": []}
    assert propose.approve_action(a["id"], "luca")["status"] == "approved"


def test_self_check_lists_unsupported_statements_and_is_cached(monkeypatch):
    a = propose.for_user("luca")[0]
    gemini_returns(monkeypatch, {"unsupported": ["paid by Friday 27 Nov"]})
    r = propose.self_check(a["id"], "luca")
    assert r == {"status": "warnings", "items": ["paid by Friday 27 Nov"]}
    monkeypatch.setattr(llm, "_generate", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called twice")))
    assert propose.self_check(a["id"], "luca")["items"] == ["paid by Friday 27 Nov"]          # cached on the action
    assert propose.self_check(a["id"], "sara")["status"] == "skipped"                         # only the approver
    propose.edit_action(a["id"], "luca", a["subject"], "Hi Giulia, can you approve INV-2026-0912 today?")
    assert "self_check" not in next(x for x in store.actions() if x["id"] == a["id"])         # re-checked after an edit
    monkeypatch.setattr(llm, "_generate", lambda *a, **k: {"unsupported": []})
    assert propose.self_check(a["id"], "luca")["status"] == "ok"
    assert propose.approve_action(a["id"], "luca")["status"] == "approved"                    # never blocks


def test_self_check_sends_only_what_the_approver_may_see(monkeypatch):
    seen = {}

    def capture(system, prompt, temperature):
        seen["prompt"] = prompt
        return {"unsupported": []}

    monkeypatch.setattr(llm, "configured_mode", lambda: "gemini")
    monkeypatch.setattr(llm, "_generate", capture)
    a = propose.for_user("sara")[0]                       # tech: the certificate request to Marco
    propose.self_check(a["id"], "sara")
    assert "chat-007" in seen["prompt"] and "412,000" not in seen["prompt"]


# ---------- 2. quote check on new memory ----------
def test_extractor_facts_without_an_exact_quote_are_dropped(monkeypatch):
    gemini_returns(monkeypatch, {"facts": [
        {"fact": "The gateway visit is on Thursday at 07:00.", "quote": "Thursday 07:00 works for the gateway visit"},
        {"fact": "Langhe Viva will pay EUR 50,000 extra.", "quote": "we will pay 50,000 extra"}],
        "alert": "Langhe Viva confirmed Thursday 07:00.", "suspicious": False, "urgent": False})
    out = watch.new_email_arrives()
    kept = [m for m in store.memory() if m["id"] in out["pending"]]
    assert [m["fact"] for m in kept] == ["The gateway visit is on Thursday at 07:00."]
    assert kept[0]["quote"] == "Thursday 07:00 works for the gateway visit"
    assert any(r["event"] == "memory_candidate_dropped" and "50,000" in r["fact"] for r in audit.read())


def test_quote_check_is_word_for_word():
    text = "Paolo, thanks for calling. Thursday 07:00 works for the gateway visit."
    assert memory.quote_in_source("thursday  07:00 WORKS for the gateway visit", text)
    assert not memory.quote_in_source("Thursday 08:00 works for the gateway visit", text)
    assert not memory.quote_in_source("", text) and not memory.quote_in_source("Paolo", text)


def test_offline_extraction_quotes_its_own_source():
    out = watch.new_email_arrives()
    m = next(x for x in store.memory() if x["id"] == out["pending"][0])
    src = store.source_by_id()["email-010"]["text"]
    assert m["quote"] and memory.quote_in_source(m["quote"], src)


def test_a_flagged_number_needs_a_written_reason():
    item = memory.add_pending("Langhe Viva has 400 sensors on GW-07.", ["chat-001"], ["tech", "sales"])
    assert memory.number_warnings(item)
    with pytest.raises(ValueError):
        memory.approve(item["id"], "davide")
    assert memory.approve(item["id"], "davide", reason="Counted on site.")["status"] == "approved"


# ---------- 3. outbox privacy ----------
def test_outbox_shows_an_item_only_to_people_who_may_see_its_sources():
    pay = next(a for a in propose.for_user("luca") if a["to"] == "giulia")
    propose.approve_action(pay["id"], "luca")                  # finance sources: task-002, email-001
    cert = next(a for a in propose.for_user("sara") if a["to"] == "marco")
    propose.approve_action(cert["id"], "sara")                 # tech sources: task-004, chat-007
    ids = lambda u: {o["id"] for o in propose.outbox_for(u)}  # noqa: E731
    assert pay["id"] in ids("luca") and pay["id"] in ids("giulia") and pay["id"] in ids("elena")
    assert pay["id"] not in ids("sara") and pay["id"] not in ids("paolo") and pay["id"] not in ids("davide")
    assert cert["id"] in ids("marco") and cert["id"] not in ids("giulia") and cert["id"] in ids("elena")


# ---------- 4. the timer ----------
def test_timer_never_runs_under_pytest():
    assert not brief.timer_enabled()
    assert brief.maybe_sweep() is False


def test_timer_sweeps_when_the_interval_has_passed(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("JARVIS_SWEEP_MINUTES", "30")
    assert brief.minutes_to_next_sweep() in (29, 30)           # the fixture just swept
    assert brief.maybe_sweep() is False
    monkeypatch.setattr(store, "last_swept", lambda: 0.0)      # 30+ minutes ago
    assert brief.minutes_to_next_sweep() == 0
    assert brief.maybe_sweep() is True
    assert any(r["event"] == "sweep" and r.get("trigger") == "timer" for r in audit.read())
    monkeypatch.setenv("JARVIS_SWEEP_MINUTES", "0")
    assert not brief.timer_enabled()


def test_a_re_sweep_keeps_alerts_and_escalation_drafts():
    watch.new_email_arrives(store.demo_events()["urgent_email"])
    fix = [a["id"] for a in propose.for_user("elena") if a["status"] == "awaiting_approval"]
    assert fix and store.briefs()["paolo"].get("alerts")
    brief.sweep("timer")
    assert store.briefs()["paolo"].get("alerts")
    assert set(fix) <= {a["id"] for a in propose.for_user("elena")}


def test_reset_counts_as_a_fresh_sweep():
    store.reset_demo()
    assert store.last_swept() is None
    store.mark_swept()
    assert store.last_swept() is not None


# ---------- 5. strict matching for "not for your role" ----------
def test_not_for_your_role_needs_a_clear_confident_match():
    assert "available for your role" in answer.ask("sara", "What is our cash runway?")["answer"]
    # a reworded guess that only grazes the restricted fact: plain "I don't know"
    for q in ("Tell me about cash", "What is the burn?", "Is the senior hire budget bigger than cash?"):
        r = answer.ask("sara", q)
        assert not r["known"] and r["answer"].startswith("I don't know"), q
    assert answer.confident_match("runway cash", [{"id": "a", "fact": "cash runway is long"},
                                                  {"id": "b", "fact": "runway cash is short"}]) is None   # a tie


def test_audit_rows_follow_the_role_filter_in_the_brain_data():
    answer.ask("giulia", "What is our cash runway?")
    rows = [r for r in audit.read() if r.get("user") == "giulia" and r["event"] == "ask"]
    assert rows and rows[-1]["cited"] == ["mem-002"]


# ---------- the company is a data folder ----------
def test_data_folder_is_selectable_and_defaults_to_filare():
    assert store.DATA.name == "data_filare" and store.SNAPSHOT.name == "data_filare"
    assert (store.SNAPSHOT / "briefs.json").exists()


def test_stripe_hides_when_the_company_has_no_stripe_data(monkeypatch, tmp_path):
    from brain import stripe_sync
    assert stripe_sync.connected()
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    import shutil
    company = tmp_path / "data_nostripe"
    shutil.copytree(store.DATA, company, ignore=shutil.ignore_patterns("stripe_charges.json"))
    monkeypatch.setattr(store, "DATA", company)           # same company, but no Stripe export
    assert not stripe_sync.connected()
    with pytest.raises(RuntimeError, match="not connected"):
        stripe_sync.sync("giulia")
