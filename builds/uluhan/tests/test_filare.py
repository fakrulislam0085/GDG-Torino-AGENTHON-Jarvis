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


def test_model_cannot_omit_recipient_outage_risk(demo, monkeypatch):
    client, store = demo
    from brain import agents, tools as T

    def empty_model_brief(ctx, _system, _prompt, _offline):
        T.t_submit_brief(ctx, [])

    store.processed_sources.add("email-002")
    monkeypatch.setattr(agents, "_run", empty_model_brief)
    agents.brief(store, "davide")
    item = store.briefs["davide"]["items"][0]
    assert item["citations"][0]["id"] == "email-002" and "40 of 120" in item["why"]


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


def test_event_probe_is_visible_but_locked_for_wrong_persona(demo):
    client, _ = demo
    luca = {event["id"]: event for event in state(client, "luca")["pending_events"]}
    sara = {event["id"]: event for event in state(client, "sara")["pending_events"]}
    assert luca["email-008"]["allowed"] is False
    assert sara["email-008"]["allowed"] is True


def test_live_check_hydrates_summary_steps(demo):
    client, _ = demo
    from live_checks import _full_run
    summary = client.post("/api/sweep").json()["runs"][0]
    assert isinstance(summary["steps"], int)
    assert isinstance(_full_run(client, summary)["steps"], list)


def test_visible_ui_guards_are_present(demo):
    client, _ = demo
    html = client.get("/").text
    assert 'timeout: 75000' in html
    assert 'action !== "voice" || S.voice' in html
    assert 'await audio.play()' in html and 'browser blocked audio playback' in html


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


def test_archived_flag_comes_from_the_date_not_the_id():
    from brain import shared
    d = shared.load_shared()
    live = {e["id"]: e["source"] for e in d["live_events"]}
    assert live["email-006"]["archived"] is True            # 4 Aug vs 23 Nov sweep
    assert live["email-008"]["archived"] is False
    assert not any(s.get("archived") for s in d["sources"] if s["type"] == "mail")
    import inspect
    from brain import agents
    assert "email-006" not in inspect.getsource(agents)   # no demo ids in agent logic


# Business rules are generic: driven by org chart + approved memory, not demo ids ---------------------
def _rule_ctx(store, person):
    from brain import agents, tools as T
    tr = agents.Trace("brief", person, "test", store.access(person), store.clock)
    return T.Ctx(store, "brief", person, store.person(person)["role"], tr)


def _add_overdue_mail_to(store, person, audience):
    store.sources["mail-x"] = {"id": "mail-x", "type": "mail", "audience": audience, "ts": "2026-11-22T09:00:00+01:00",
                               "stage": "overnight", "from": "billing@cloudhost.example", "to": "", "recipient_ids": [person],
                               "title": "Hosting invoice overdue", "body": "Your hosting invoice H-77 for EUR 900 is overdue."}
    store.memory["mem-x"] = {"id": "mem-x", "key": "hosting.invoice", "topic": "Hosting invoice", "audience": audience,
                             "fact": "Hosting invoice H-77 for EUR 900 is overdue.", "status": "approved",
                             "source_id": "mail-x", "source_ids": ["mail-x"], "quote": "overdue",
                             "decided_by": "marco", "decided_at": store.clock}
    store.processed_sources.add("mail-x")


def test_review_rule_works_for_any_team():
    from brain import agents
    from brain.store import Store
    s = Store()
    _add_overdue_mail_to(s, "sara", ["tech"])
    item = agents._review_request(_rule_ctx(s, "sara"))
    assert item and s.proposals[item["proposal_id"]]["to"] == s.person("marco")["email"]   # Sara's lead: CTO
    assert agents._review_request(_rule_ctx(s, "marco")) is None                            # leads don't escalate
    assert agents._review_request(_rule_ctx(s, "elena")) is None                            # not a recipient


def test_agent_code_has_no_demo_ids_or_names():
    import inspect, re
    from brain import agents, server, store, tools
    for mod in (agents, server, store):
        src = inspect.getsource(mod)
        assert not re.search(r'"(email|mem|chat|task|doc)-\d|"(luca|giulia|marco|sara|davide|paolo|elena)"', src), mod.__name__


# Change control: approved facts change only by authority, never by chronology alone ---------------
def _conflict(client, person):
    return next(a for a in state(client, person)["alerts"] if a["kind"] == "conflict")


def test_decision_receipt_for_archived_budget_claim(demo):
    client, store = demo
    client.post("/api/events/email-006")
    alert = _conflict(client, "giulia")
    r = alert["receipt"]
    assert "18,000" in r["current"]["fact"] and "12,000" in r["claim"]["fact"]
    assert r["current"]["approved_by"].startswith("Giulia") and r["current"]["status"] == "approved"
    assert {s["id"] for s in r["current"]["sources"]} == {"email-004", "email-005"}
    assert r["claim"]["dated"] == "2026-08-04"
    assert any("Older evidence" in x for x in r["reasons"])
    assert r["record_changed"] is False and "unchanged" in r["outcome"]
    assert r["you_can_approve"] is False and r["you_can_reject"] is True
    # The approval endpoint refuses it too, for everyone.
    for person in ("giulia", "elena"):
        assert client.post(f"/api/memory/{alert['candidate_id']}/approve", json={"person": person}).status_code in (403, 409)
    # Final proof: the budget answer is still the approved figure, with its citation.
    answer = ask(client, "giulia", "What is the Q1 2027 cloud budget?")["answer"]
    assert "18,000" in answer["text"] and answer["citations"][0]["id"] == "mem-001"
    # Rejecting the claim is recorded and the record stays.
    assert client.post(f"/api/memory/{alert['candidate_id']}/reject", json={"person": "sara"}).status_code == 200
    r = _conflict(client, "giulia")["receipt"]
    assert r["record_changed"] is False and r["outcome"].startswith("Claim rejected by Sara")


def _newer_claim(client):
    """Use the same build-local event and ingestion path as the live demo."""
    response = client.post("/api/events/mail-new")
    assert response.status_code == 200 and len(response.json()["runs"]) == 1
    alert = next(a for a in state(client, "sara")["alerts"] if a["source_id"] == "mail-new")
    assert client.post("/api/events/mail-new").json()["runs"] == []
    return alert["candidate_id"]


def test_newer_claim_needs_authority_not_recency(demo):
    client, store = demo
    cid = _newer_claim(client)
    # Sara can see the budget but has no authority over it.
    r = client.post(f"/api/memory/{cid}/approve", json={"person": "sara"})
    assert r.status_code == 403 and "Being newer is not enough" in r.json()["detail"]
    assert store.memory["mem-001"]["status"] == "approved"
    receipt = _conflict(client, "sara")["receipt"]
    assert receipt["you_can_approve"] is False and not any("Older evidence" in x for x in receipt["reasons"])
    assert any("Giulia Ferrero" in x for x in receipt["reviewers"])
    # The CFO who approved it can.
    assert _conflict(client, "giulia")["receipt"]["you_can_approve"] is True
    assert client.post(f"/api/memory/{cid}/approve", json={"person": "giulia"}).status_code == 200
    assert store.memory["mem-001"]["status"] == "superseded"
    assert _conflict(client, "giulia")["receipt"]["record_changed"] is True


def test_two_receipts_preserve_rejection_after_later_budget_approval(demo):
    client, store = demo
    question = "What is the Q1 2027 cloud budget?"
    first = ask(client, "giulia", question)["answer"]
    assert "18,000" in first["text"] and first["citations"][0]["source_id"] == "email-005"
    client.post('/api/events/email-006')
    archive = _conflict(client, 'sara')['candidate_id']
    assert client.post(f'/api/memory/{archive}/reject', json={'person': 'sara'}).status_code == 200
    draft, = state(client, "giulia")["proposals"]
    assert draft["status"] == "pending" and draft["citations"][0]["id"] == "mem-001"
    newer = _newer_claim(client)
    before = ask(client, 'giulia', question)['answer']
    assert '18,000' in before['text'] and before['citations'][0]['id'] == 'mem-001'
    assert client.post(f'/api/memory/{newer}/approve', json={'person': 'sara'}).status_code == 403
    assert client.post(f'/api/memory/{newer}/approve', json={'person': 'giulia'}).status_code == 200
    receipts = {a['candidate_id']: a['receipt'] for a in state(client, 'giulia')['alerts']}
    rejected, accepted = receipts[archive], receipts[newer]
    assert rejected['claim']['status'] == 'rejected'
    assert rejected['outcome'].startswith('Claim rejected by Sara')
    assert rejected['record_changed'] is False
    assert accepted['record_changed'] is True
    assert accepted['outcome'].startswith('Record replaced after review by Giulia')
    assert accepted['current']['status'] == 'superseded'
    assert accepted['claim']['status'] == 'approved'
    assert store.memory['mem-001']['superseded_by'] == newer
    after = ask(client, 'giulia', question)['answer']
    assert '25,000' in after['text'] and after['citations'][0]['id'] == newer
    assert after['citations'][0]['source_id'] == 'mail-new'

    release = f"/api/proposals/{draft['id']}/approve"
    assert client.post(release, json={"person": "sara"}).status_code == 403
    for _ in range(2):
        assert client.post(release, json={"person": "giulia"}).status_code == 409
    assert store.proposals[draft["id"]]["status"] == "withdrawn" and not store.outbox
    assert sum(a["action"] == "proposal.withdrawn" for a in store.audit) == 1


def test_archived_rejection_preserves_valid_budget_draft(demo):
    client, store = demo
    client.post("/api/events/email-006")
    client.post(f"/api/memory/{_conflict(client, 'sara')['candidate_id']}/reject", json={"person": "sara"})
    draft, = state(client, "giulia")["proposals"]
    path = f"/api/proposals/{draft['id']}/approve"
    assert client.post(path, json={"person": "giulia"}).status_code == 200
    assert client.post(path, json={"person": "giulia"}).status_code == 409
    assert len(store.outbox) == 1


def _open_budget_reviews(client):
    reviews = {}
    for source_id, reviewer in (("mail-new", "giulia"), ("slack-budget", "marco")):
        path = f"/api/events/{source_id}"
        assert len(client.post(path).json()["runs"]) == 1
        assert client.post(path).json()["runs"] == []
        workspace = state(client, reviewer)
        alert, = [a for a in workspace["alerts"] if a["source_id"] == source_id]
        candidate, = [m for m in workspace["candidates"] if m["source_id"] == source_id]
        assert candidate["reviewed_against"] == "mem-001"
        receipt = alert["receipt"]
        assert receipt["current"]["id"] == receipt["original_revision"] == "mem-001"
        assert receipt["you_can_approve"] and "18,000" in receipt["current"]["fact"]
        reviews[source_id] = (f"/api/memory/{alert['candidate_id']}/approve",
                              {"person": reviewer, "reviewed_against": receipt["current"]["id"]})
    return reviews


def test_competing_reviews_and_fresh_reassessment(demo):
    client, store = demo
    client.post("/api/sweep")
    client.post("/api/events/email-006")
    draft, = state(client, "giulia")["proposals"]
    invoice, = state(client, "luca")["proposals"]
    assert draft["citations"][0]["id"] == "mem-001" and draft["status"] == "pending"
    client.post(f"/api/memory/{_conflict(client, 'sara')['candidate_id']}/reject", json={"person": "sara"})
    # Ordinary acknowledgement on the same topic, with no new decision.
    followup = dict(store.sources["email-005"], id="followup", body="Thanks, the report is on its way.")
    store.live_events["followup"] = {"id": "followup", "source": followup, "label": "Follow-up",
                                     "fallback_candidates": []}
    assert client.post("/api/events/followup").status_code == 200
    assert not any(a["source_id"] == "followup" for a in store.alerts)
    assert store.proposals[invoice["id"]]["status"] == "pending"
    reviews = _open_budget_reviews(client)
    email, giulia = reviews["mail-new"]
    slack, marco = reviews["slack-budget"]
    assert client.post(slack, json={"person": "sara", "reviewed_against": "mem-001"}).status_code == 403
    accepted = client.post(email, json=giulia)
    assert accepted.status_code == 200
    winner = accepted.json()["memory"]["id"]
    for original_review in (marco, {"person": "marco"}):
        response = client.post(slack, json=original_review)
        assert response.status_code == 409
        assert winner in response.json()["detail"] and "25,000" in response.json()["detail"]
    pending, = [a["receipt"] for a in state(client, "marco")["alerts"] if a["source_id"] == "slack-budget"]
    assert pending["claim"]["status"] == "candidate" and not pending["record_changed"]
    assert pending["current"]["id"] == winner and pending["original_revision"] == "mem-001"
    assert pending["current"]["sources"][0]["id"] == "mail-new"
    assert pending["claim"]["sources"][0]["id"] == "slack-budget"
    assert any(a["actor"] == "marco" and a["action"] == "memory.review_stale" for a in store.audit)
    assert client.post(slack, json={"person": "sara", "reviewed_against": winner}).status_code == 403
    assert client.post(f"/api/proposals/{draft['id']}/approve", json={"person": "giulia"}).status_code == 409
    assert not store.outbox
    assert client.post(f"/api/proposals/{invoice['id']}/approve", json={"person": "luca"}).status_code == 200
    assert [o["proposal_id"] for o in store.outbox] == [invoice["id"]]
    # Marco must explicitly review against the €25,000 decision before accepting Slack.
    assert client.post(slack, json={**marco, "reviewed_against": winner}).status_code == 200
    receipts = {a["source_id"]: a["receipt"] for a in state(client, "marco")["alerts"]}
    assert receipts["mail-new"]["record_changed"] and receipts["mail-new"]["claim"]["status"] == "superseded"
    assert receipts["slack-budget"]["record_changed"] and receipts["slack-budget"]["current"]["id"] == winner
    assert receipts["slack-budget"]["original_revision"] == "mem-001"
    assert receipts["email-006"]["outcome"].startswith("Claim rejected by Sara")


def test_simultaneous_budget_approvals_have_one_winner(demo):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    client, store = demo
    reviews = _open_budget_reviews(client)
    barrier = Barrier(2)

    def publish(review):
        path, body = review
        barrier.wait(timeout=5)
        return client.post(path, json=body).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(publish, reviews.values())) == [200, 409]
    assert len([a for a in store.audit if a["action"] == "memory.superseded"]) == 1
    assert len([m for m in store.memory.values() if m["key"] == "cloud.budget.q1.2027"
                and m["status"] == "approved"]) == 1


def test_orchard_shadow_workspace(demo):
    from billing_shadow import replay
    replay(demo[0])


def test_reject_orchard_correction_releases_only_the_original_hold(demo):
    client, _ = demo
    client.post("/api/events/orchard-acceptance")
    client.post("/api/events/orchard-correction")
    workspace = state(client, "giulia")
    draft, = workspace["proposals"]
    alert, = workspace["alerts"]
    path = f"/api/memory/{alert['candidate_id']}/reject"
    assert client.post(path, json={"person": "luca"}).status_code == 403
    assert client.post(path, json={"person": "giulia"}).status_code == 200
    resumed, = state(client, "giulia")["proposals"]
    assert resumed["id"] == draft["id"] and resumed["status"] == "pending"
    assert client.post(f"/api/proposals/{draft['id']}/approve", json={"person": "giulia"}).status_code == 200


def test_old_email_copies_preserve_fresh_orchard_handoff(demo):
    client, _ = demo
    client.post("/api/events/orchard-acceptance")
    client.post("/api/events/orchard-correction")
    alert, = state(client, "giulia")["alerts"]
    client.post(f"/api/memory/{alert['candidate_id']}/approve", json={"person": "giulia"}).raise_for_status()
    for name in ("followup", "duplicate"):
        client.post(f"/api/events/orchard-{name}").raise_for_status()
        old, fresh = state(client, "giulia")["proposals"]
        assert old["status"] == "withdrawn" and fresh["status"] == "pending"
        assert fresh["citations"][0]["id"] == alert["candidate_id"]
