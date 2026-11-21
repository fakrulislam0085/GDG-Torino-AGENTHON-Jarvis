"""Offline tests for the Today header counters, the sidebar nav badges and the one-tap question chips (ui/counts.py).
Run from builds/best: ..\\arif\\.venv\\Scripts\\python -m pytest tests -q"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["BRAIN_MODE"] = "offline"
os.environ["JARVIS_DATA"] = "data_filare"
if "brain.store" not in sys.modules:          # never the real state: the fixture resets the demo
    os.environ["BRAIN_STATE_DIR"] = tempfile.mkdtemp(prefix="brain-best-test-")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from brain import access, brief, llm, memory, propose, store  # noqa: E402
from ui import counts  # noqa: E402


@pytest.fixture(autouse=True)
def fresh():
    store.reset_demo()
    llm.reset_breaker()
    brief.sweep()
    yield


def test_brief_count_is_this_users_brief_only():
    for u in store.people():
        b = store.briefs().get(u, {})
        assert counts.brief_items(u) == len(b.get("alerts", [])) + len(b.get("items", []))
    assert counts.brief_items("nobody") == 0


def test_to_review_counts_only_items_the_user_can_see_and_decide():
    for u in store.people():
        visible = {m["id"] for m in access.visible(store.memory(), u)}
        decidable = [m for m in store.memory() if m["status"] == "pending" and m["id"] in visible and memory.can_review(m["id"], u)]
        assert counts.to_review(u) == len(decidable)
        assert counts.to_review(u) <= len(memory.pending_for(u))
    # Sara (backend engineer) sees pending items but may decide none of them: no badge for her
    assert memory.pending_for("sara") and counts.to_review("sara") == 0


def test_to_review_never_counts_an_item_outside_the_role():
    hidden = [m for m in store.memory() if m["status"] == "pending" and not access.can_see(m, "paolo")]
    assert hidden, "demo data should hide at least one pending item from Paolo"
    before = counts.to_review("paolo")
    assert before == sum(memory.can_review(m["id"], "paolo") for m in memory.pending_for("paolo"))
    assert all(m["id"] not in {x["id"] for x in memory.pending_for("paolo")} for m in hidden)


def test_to_review_drops_after_approve_and_reject():
    u = "davide"
    n = counts.to_review(u)
    mine = [m["id"] for m in memory.pending_for(u) if memory.can_review(m["id"], u)]
    memory.approve(mine[0], u)
    assert counts.to_review(u) == n - 1
    memory.reject(mine[1], u, "Not right, the source says otherwise")
    assert counts.to_review(u) == n - 2


def test_pending_actions_are_only_the_users_and_drop_after_a_decision():
    for u in store.people():
        assert counts.pending_actions(u) == sum(a["status"] == "awaiting_approval" for a in store.actions() if a["proposed_to"] == u)
    assert counts.pending_actions("luca") == 1 and counts.pending_actions("elena") == 0
    aid = next(a["id"] for a in propose.for_user("luca") if a["status"] == "awaiting_approval")
    propose.approve_action(aid, "luca")
    assert counts.pending_actions("luca") == 0
    sid = next(a["id"] for a in propose.for_user("sara") if a["status"] == "awaiting_approval")
    propose.reject_action(sid, "sara", "Not now, wrong customer")
    assert counts.pending_actions("sara") == 0


def test_counts_bundle():
    assert counts.counts("luca") == {"brief": counts.brief_items("luca"), "review": counts.to_review("luca"),
                                     "actions": counts.pending_actions("luca")}


def test_chip_questions_from_data_deduplicated_and_capped():
    qs = counts.chip_questions(store.demo())
    assert qs == ["When does the Langhe fix roll out?", "What is our cash runway?", "What is the office Wi-Fi password?"]
    demo = {"checks": [{"question": ""}, {"question": "A?"}, {"question": "a ?"}, {"question": "B"}, {"question": "C"},
                       {"question": "D"}], "ask_placeholder": "E"}
    assert counts.chip_questions(demo) == ["A?", "B", "C", "D"]
    assert counts.chip_questions({}) == []
