"""Offline tests for the "How your 08:00 email is made" panel counts (ui/pipeline.py): every number respects the role filter.
Run from jarvis-your-company-brain: ..\\builds\\arif\\.venv\\Scripts\\python -m pytest -q"""
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

os.environ["BRAIN_MODE"] = "offline"
os.environ.setdefault("JARVIS_DATA", "data_filare")
if "brain.store" not in sys.modules:          # never the real state: the fixture resets the demo
    os.environ["BRAIN_STATE_DIR"] = tempfile.mkdtemp(prefix="brain-pipeline-test-")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from brain import access, brief, guard, llm, memory, store  # noqa: E402
from ui import counts, pipeline  # noqa: E402


@pytest.fixture(autouse=True)
def fresh():
    store.reset_demo()
    llm.reset_breaker()
    brief.sweep()
    yield


def test_source_counts_match_access_visible_per_kind():
    for u in store.people():
        seen = Counter(s["kind"] for s in access.visible(store.sources(), u))
        rows = pipeline.source_counts(u)
        for r in rows:
            assert r["n"] == seen.get(r["kind"], 0)
        assert pipeline.pipeline(u)["read"] == sum(seen.get(r["kind"], 0) for r in rows)


def test_source_counts_never_exceed_what_exists_and_respect_roles():
    total = Counter(s["kind"] for s in store.sources())
    for u in store.people():
        for r in pipeline.source_counts(u):
            assert r["n"] <= total[r["kind"]]


def test_counts_differ_by_role_when_acls_differ():
    reads = {u: pipeline.pipeline(u)["read"] for u in store.people()}
    ceo = store.ceo()
    assert ceo in reads
    assert all(reads[u] <= reads[ceo] for u in reads)          # the CEO sees everything
    assert any(reads[u] < reads[ceo] for u in reads)            # someone sees less: the filter bites


def test_guard_and_memory_counts_use_the_role_filter():
    for u in store.people():
        vis = access.visible(store.sources(), u)
        assert pipeline.guard_blocked(u) == sum(1 for s in vis if s["kind"] in ("email", "chat") and guard.suspicious(s["text"]))
        p = pipeline.pipeline(u)
        vis_mem = access.visible(store.memory(), u)
        assert p["approved"] == sum(m["status"] == "approved" for m in vis_mem) == len(memory.approved_for(u))
        assert p["waiting"] == sum(m["status"] == "pending" for m in vis_mem)
        assert p["brief"] == counts.brief_items(u)


def test_tool_names_and_actions_are_honest():
    names = pipeline.tool_names()
    assert set(names) == {"email", "chat", "task", "doc"}
    for a in pipeline.actions_live():
        assert isinstance(a["live"], bool)
    assert "Slack" in pipeline.NEXT and "Notion" in pipeline.NEXT
