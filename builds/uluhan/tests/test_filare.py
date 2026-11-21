"""The shared company is the default. Exercise the actual jury flow and evidence boundaries."""
import json

from fastapi.testclient import TestClient
import pytest

from brain import server, tools
from brain.agents import Trace
from brain.store import Store


@pytest.fixture
def demo(monkeypatch):
    store = Store()
    monkeypatch.setattr(server, "store", store)
    monkeypatch.setenv("BRAIN_MODE", "offline")
    with TestClient(server.app) as client:
        yield client, store


def state(client, person):
    response = client.get("/api/state", params={"person": person})
    assert response.status_code == 200
    return response.json()


def ask(client, person, question):
    response = client.post("/api/ask", json={"person": person, "question": question})
    assert response.status_code == 200
    return response.json()


def test_shared_morning_dm_and_approval(demo):
    client, store = demo
    assert state(client, "luca")["brief"] is None
    assert state(client, "luca")["company"] == "Filare Labs S.r.l."
    response = client.post("/api/sweep")
    assert response.status_code == 200
    assert len([r for r in response.json()["runs"] if r["agent"] == "brief"]) == 7
    luca, davide = state(client, "luca"), state(client, "davide")
    assert luca["brief"]["items"][0]["citations"][0]["id"] == "email-001"
    assert davide["brief"]["items"][0]["citations"][0]["id"] == "email-002"
    assert "40 of 120" in davide["brief"]["items"][0]["why"]
    assert client.get("/").text.count("Memory review")
    proposal = luca["brief"]["items"][0]["proposal_id"]
    assert [p["id"] for p in luca["proposals"]] == [proposal]
    assert luca["outbox"] == []
    assert client.post(f"/api/proposals/{proposal}/approve", json={"person": "giulia"}).status_code == 403
    assert client.post(f"/api/proposals/{proposal}/approve", json={"person": "luca"}).status_code == 200
    assert client.post(f"/api/proposals/{proposal}/approve", json={"person": "luca"}).status_code == 409
    assert client.post("/api/sweep").status_code == 200
    assert len(state(client, "luca")["outbox"]) == len(store.proposals) == 1


def test_curation_and_source_change_what_sara_knows(demo):
    client, _ = demo
    question = "When does the Langhe fix roll out?"
    assert ask(client, "sara", question)["answer"]["status"] == "unknown"
    assert client.post("/api/memory/mem-p01/approve", json={"person": "sara"}).status_code == 200
    assert client.post("/api/memory/mem-p02/reject", json={"person": "sara"}).status_code == 200
    accepted = ask(client, "sara", question)["answer"]
    assert "26 Nov 2026 at 07:00" in accepted["text"]
    assert accepted["citations"][0]["source_id"] == "chat-003"
    assert ask(client, "sara", "What is Langhe Viva's contract value?")["answer"]["status"] == "unknown"


def test_role_coverage_and_no_restricted_topic_disclosure(demo):
    client, store = demo
    question = "What is our cash runway?"
    for person in ("giulia", "elena"):
        answer = ask(client, person, question)["answer"]
        assert "about 7 months" in answer["text"]
        assert answer["citations"][0]["source_id"] == "email-003"
    invisible = ask(client, "sara", question)
    missing = ask(client, "sara", "What is our Q2 2027 cloud budget?")
    assert invisible["answer"] == missing["answer"]
    for view in (invisible, state(client, "sara")):
        assert all(value not in json.dumps(view) for value in ("412,000", "mem-002", "Cash runway and net burn"))
    assert client.get(f"/api/runs/{store.runs[0]['id']}", params={"person": "sara"}).status_code == 404


def test_archived_budget_cannot_replace_approved_evidence(demo):
    client, store = demo
    assert client.post("/api/events/email-006").status_code == 200
    assert client.post("/api/events/email-006").json()["runs"] == []
    alert, = state(client, "sara")["alerts"]
    assert alert["source_id"] == "email-006"
    assert state(client, "paolo")["alerts"] == []
    assert store.clock == store.seed["clock_start"]
    path = f"/api/memory/{alert['candidate_id']}"
    assert client.post(path + "/approve", json={"person": "giulia"}).status_code == 409
    assert client.post(path + "/reject", json={"person": "giulia"}).status_code == 200
    answer = ask(client, "sara", "What is the Q1 2027 cloud budget?")["answer"]
    assert "EUR 18,000, approved" in answer["text"]
    assert answer["citations"][0]["id"] == "mem-001"


def test_flagged_email_leaves_no_memory_or_recipient(demo):
    client, store = demo
    assert client.post("/api/events/email-008").status_code == 200
    assert [a["source_id"] for a in state(client, "sara")["alerts"]] == ["email-008"]
    assert state(client, "giulia")["alerts"] == []
    assert not store.proposals
    assert not any(m["source_id"] == "email-008" for m in store.memory.values())
    assert "it-support@filare-helpdesk.example" not in tools.allowed_recipients(store, store.access("sara"))


def test_conflicting_candidate_does_not_cross_audience(demo):
    _, store = demo
    source = store.sources["email-009"]
    trace = Trace("ingest", "system", "fixture", source["audience"], store.clock)
    ctx = tools.Ctx(store, "ingest", "system", None, trace, source_id=source["id"])
    # A new sales-only source cannot become a revision of otherwise approved all-company memory.
    tools.t_propose_memory(ctx, "team.lunch", "Team lunch", source["body"], source["body"])
    assert not store.alerts
    assert store.memory["mem-009"]["status"] == "approved"
    assert source["body"] not in json.dumps(store.visible_memory(["tech"]))


def test_reset_cannot_interleave_with_agent_run(demo):
    client, store = demo
    with store.agent_operation:
        assert client.post("/api/reset").status_code == 409
