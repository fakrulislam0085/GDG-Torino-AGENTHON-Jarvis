"""The cold open, ported onto the current build: a Wednesday-night frost warning holds the waiting customer reply
and raises one internal request to the engineer. Offline, on the Filare Labs data.

Run from jarvis-your-company-brain: .venv/bin/python -m pytest tests/test_cold_open.py -q
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["BRAIN_MODE"] = "offline"
os.environ["JARVIS_DATA"] = "data_filare"
os.environ["BRAIN_STATE_DIR"] = tempfile.mkdtemp(prefix="brain-cold-open-test-")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from brain import brief, hold, propose, store, watch  # noqa: E402

CUSTOMER = "agronomo@langheviva.example"
ENGINEER = "davide"
APPROVER = "paolo"


@pytest.fixture(autouse=True)
def fresh():
    store.reset_demo()
    brief.sweep()
    yield


def frost() -> dict:
    return store.demo_events()["frost_warning"]


def reply() -> dict:
    return next(a for a in store.actions() if a["type"] == "reply_draft" and a["to"] == CUSTOMER)


def internal() -> list:
    return [a for a in propose.for_user(APPROVER) if a["to"] == ENGINEER and a["status"] == "awaiting_approval"]


def test_the_reply_waits_before_the_warning():
    assert reply()["status"] == "awaiting_approval"
    assert store.outbox() == [] and hold.case_context(APPROVER) == []


def test_the_frost_warning_holds_the_reply_and_raises_one_internal_request():
    out = watch.new_email_arrives(frost())
    assert out["status"] == "ingested"
    d = reply()
    assert d["status"] == "held"
    assert d["hold_sources"] == ["email-101", "chat-003"]           # the two real records, in date order
    assert "email-101" in d["hold_reason"]
    assert [e["cites"] for e in d["evidence"]] == [["email-101"], ["chat-003"]]
    req = internal()
    assert len(req) == 1 and req[0]["proposed_to"] == APPROVER
    assert store.outbox() == []                                      # nothing is sent automatically


def test_a_held_reply_is_refused_and_never_reaches_the_outbox():
    watch.new_email_arrives(frost())
    d = reply()
    propose.approve_action(d["id"], APPROVER)                        # refused: a held draft is not decidable
    assert store.outbox() == []
    assert next(a for a in store.actions() if a["id"] == d["id"])["status"] == "held"


def test_approving_only_the_internal_request_sends_one_item_to_the_engineer():
    watch.new_email_arrives(frost())
    req = internal()[0]
    with pytest.raises(PermissionError):
        propose.approve_action(req["id"], ENGINEER)                  # only the person it was proposed to
    propose.approve_action(req["id"], APPROVER)
    assert [o["to"] for o in store.outbox()] == [ENGINEER]           # exactly one item, to the engineer
    assert reply()["status"] == "held"                               # the customer reply stays held


def test_the_case_context_surfaces_only_after_the_email_and_only_to_those_who_see_it():
    assert hold.case_context(APPROVER) == []
    watch.new_email_arrives(frost())
    ctx = hold.case_context(APPROVER)
    assert ctx and any(c.get("cites") == ["email-101"] for c in ctx)
    assert any(c.get("simulated") for c in ctx)
    assert hold.case_context("luca") == []                           # finance is not part of this case


def test_the_cold_open_timeline_uses_the_real_sources_and_labels():
    watch.new_email_arrives(frost())
    html = hold.timeline(reply())
    for s in ("Customer email", "Engineering chat", "Rollout is scheduled after coverage is needed",
              "Customer reply held", "waiting on"):
        assert s in html, s
