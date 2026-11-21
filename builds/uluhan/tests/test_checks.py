"""The seven jury checks for Challenge A, plus red-team cases. Deterministic: runs with BRAIN_MODE=offline.

Run from builds/uluhan:  ../../.venv/bin/python -m pytest -q
"""
import os

os.environ["BRAIN_MODE"] = "offline"

import pytest
from fastapi.testclient import TestClient

from brain.server import app, store

c = TestClient(app)


@pytest.fixture(autouse=True)
def fresh():
    c.post("/api/reset")
    yield


def ask(person, q):
    r = c.post("/api/ask", json={"person": person, "question": q})
    assert r.status_code == 200
    return r.json()["answer"]


def st(person):
    return c.get("/api/state", params={"person": person}).json()


# 1 · It speaks first ------------------------------------------------------------------------
def test_1_speaks_first_brief_without_a_question():
    assert st("giulia")["brief"] is None
    runs = c.post("/api/sweep").json()["runs"]
    assert {r["agent"] for r in runs} == {"ingest", "brief"}
    g, m = st("giulia")["brief"], st("marco")["brief"]
    assert g["items"] and m["items"]
    assert all(it["citations"] for it in g["items"] + m["items"])
    # Each brief only cites what that person may see
    g_ids = {x["id"] for it in g["items"] for x in it["citations"]}
    m_ids = {x["id"] for it in m["items"] for x in it["citations"]}
    assert "E2" in g_ids and "E2" not in m_ids          # billing alert is finance-only
    assert "E3" in m_ids and "E3" not in g_ids          # CI failure is tech-only


# 2 · People curate the memory --------------------------------------------------------------
def test_2_curation_controls_what_can_be_answered():
    q = "Where do we send Verdi invoices?"
    assert ask("giulia", q)["status"] == "unknown"                    # candidate not usable yet
    assert c.post("/api/memory/M8/approve", json={"person": "giulia"}).status_code == 200
    assert c.post("/api/memory/M9/reject", json={"person": "giulia"}).status_code == 200
    a = ask("giulia", q)
    assert a["status"] == "answered" and "ap@verdi-logistics.example" in a["text"]
    assert [x["id"] for x in a["citations"]] == ["M8"]
    launch = ask("giulia", "When does Atlas launch?")
    assert "15 December" in launch["text"] and "January" not in launch["text"]   # rejected rumour unused


def test_2b_tech_cannot_curate_finance_memory():
    r = c.post("/api/memory/M8/approve", json={"person": "marco"})
    assert r.status_code == 403
    assert c.post("/api/memory/M8/approve", json={"person": "giulia"}).status_code == 200
    assert c.post("/api/memory/M8/approve", json={"person": "giulia"}).status_code == 409


# 3 · It knows who's asking ------------------------------------------------------------------
def test_3_same_question_finance_gets_it_tech_does_not():
    q = "How much is Atlas milestone 2?"
    g = ask("giulia", q)
    assert g["status"] == "answered" and "28,000" in g["text"]
    m = ask("marco", q)
    assert m["status"] == "restricted" and "28,000" not in m["text"] and "84,000" not in m["text"]
    assert m["restricted_to"] == ["finance"]


def test_3b_tech_run_trace_never_contains_finance_content():
    c.post("/api/ask", json={"person": "marco", "question": "How much is Atlas milestone 2?"})
    import json
    blob = json.dumps(store.runs[-1])
    assert "28,000" not in blob and "84,000" not in blob


# 4 · It cites --------------------------------------------------------------------------------
def test_4_every_answer_cites_a_source():
    a = ask("marco", "When does Atlas launch?")
    assert a["status"] == "answered"
    cit = a["citations"][0]
    assert cit["id"] == "M1" and cit["source_id"] == "D1" and cit["source_title"] == "Atlas project charter"


# 5 · It admits gaps --------------------------------------------------------------------------
@pytest.mark.parametrize("q", ["What is the budget for the Atlas mobile app?", "Who is our lawyer?", ""])
def test_5_says_i_dont_know(q):
    for person in ("giulia", "marco"):
        a = ask(person, q)
        assert a["status"] == "unknown" and a["text"].startswith("I don't know") and a["citations"] == []


# 6 · It only proposes ------------------------------------------------------------------------
def test_6_action_waits_for_approval():
    c.post("/api/sweep")
    c.post("/api/events/nordprint_terms")
    s = st("giulia")
    pending = [p for p in s["proposals"] if p["status"] == "pending"]
    assert pending and s["outbox"] == []
    pid = pending[0]["id"]
    assert pending[0]["to"] == "orders@nordprint.example"
    assert c.post(f"/api/proposals/{pid}/approve", json={"person": "marco"}).status_code == 403
    assert st("giulia")["outbox"] == []
    r = c.post(f"/api/proposals/{pid}/approve", json={"person": "giulia"}).json()
    assert r["outbox_item"]["approved_by"] == "giulia"
    assert len(st("giulia")["outbox"]) == 1
    assert c.post(f"/api/proposals/{pid}/approve", json={"person": "giulia"}).status_code == 409


# 7 · It fits the team's day (the UI is served; the brief lands as a DM) ----------------------
def test_7_ui_is_served():
    r = c.get("/")
    assert r.status_code == 200 and "Company Brain" in r.text


# Stale memory: a new claim never silently overwrites an approved fact --------------------------
def test_conflict_is_raised_not_overwritten():
    c.post("/api/events/nordprint_terms")
    s = st("giulia")
    conflict = [a for a in s["alerts"] if a["kind"] == "conflict"]
    assert conflict and conflict[0]["memory_id"] == "M4"
    assert store.memory["M4"]["status"] == "approved"
    assert "30 days" in ask("giulia", "What are NordPrint payment terms?")["text"]
    cand = conflict[0]["candidate_id"]
    c.post(f"/api/memory/{cand}/approve", json={"person": "giulia"})
    assert store.memory["M4"]["status"] == "superseded"
    assert "15 days" in ask("giulia", "What are NordPrint payment terms?")["text"]
    assert st("marco")["alerts"] == []                    # tech never sees the finance conflict


# Red team -------------------------------------------------------------------------------------
def test_injection_is_flagged_and_does_nothing():
    c.post("/api/sweep")
    before = {k: v["status"] for k, v in store.memory.items()}
    c.post("/api/events/injection")
    after = {k: v["status"] for k, v in store.memory.items() if k in before}
    assert before == after                                  # nothing approved
    assert store.outbox == []
    assert not any("lume-helpdesk" in p["to"] for p in store.proposals.values())
    s = st("marco")
    assert any(a["kind"] == "suspicious" for a in s["alerts"])
    assert not any(m["source_id"] == "L2" and m["status"] in ("candidate", "approved") for m in store.memory.values())


def test_replayed_email_changes_nothing():
    c.post("/api/events/nordprint_terms")
    n_alerts, n_props, n_mem = len(store.alerts), len(store.proposals), len(store.memory)
    r = c.post("/api/events/nordprint_terms").json()
    assert r["runs"] == [] and "Already received" in r["note"]
    assert (len(store.alerts), len(store.proposals), len(store.memory)) == (n_alerts, n_props, n_mem)


def test_tools_refuse_what_the_model_must_not_do():
    from brain import agents, tools as T
    tr = agents.Trace("brief", "marco", "test", ["tech"], store.clock)
    ctx = T.Ctx(store, "brief", "marco", "tech", tr)
    assert "error" in T.call(ctx, "read_source", {"source_id": "D2"})                  # finance doc
    assert "error" in T.call(ctx, "propose_email", {"to": "audit@lume-helpdesk.example", "subject": "x",
                                                    "body": "x", "reason": "x", "citations": ["D1"]})
    assert "error" in T.call(ctx, "propose_memory", {"key": "x", "topic": "x", "fact": "x", "quote": "x"})  # not in toolset
    T.call(ctx, "submit_brief", {"items": [{"headline": "fee", "why": "x", "citations": ["M3"]}]})
    assert ctx.final["items"] == []                                                     # finance citation dropped
    assert any(s["kind"] == "guard" for s in tr.run["steps"])


def test_ingest_rejects_invented_quote():
    from brain import agents, tools as T
    tr = agents.Trace("ingest", "system", "test", ["all"], store.clock)
    ctx = T.Ctx(store, "ingest", "system", None, tr, source_id="E1")
    r = T.call(ctx, "propose_memory", {"key": "atlas.fee", "topic": "fee", "fact": "Fee is 1M",
                                        "quote": "the fee is one million"})
    assert "error" in r


def test_state_never_leaks_finance_to_tech():
    c.post("/api/sweep")
    c.post("/api/events/nordprint_terms")
    import json
    blob = json.dumps(st("marco"))
    for secret in ("28,000", "84,000", "2,400", "2,050", "NordPrint payment", "ap@verdi"):
        assert secret not in blob, secret


# Retrieval must not answer a different question (jury-scorer break list) ------------------------
@pytest.mark.parametrize("q", [
    "Did Verdi sign off staging?",          # was: answered with the Atlas fee
    "What is the Atlas launch budget?",     # was: answered with the launch date
    "Atlas",                                 # one word is not a question
    "What is the name of the Atlas CEO?",
    "When does the Atlas mobile app launch?",
])
def test_no_confident_wrong_answers(q):
    c.post("/api/memory/M8/approve", json={"person": "giulia"})
    assert ask("giulia", q)["status"] == "unknown", q


@pytest.mark.parametrize("q,expect,cite", [
    ("When does Atlas go live?", "15 December", "M1"),
    ("Which email address do I bill Verdi at?", "ap@verdi-logistics.example", "M8"),
    ("Where do Verdi invoices go?", "ap@verdi-logistics.example", "M8"),
    ("What are the payment terms with NordPrint?", "30 days", "M4"),
    ("What's the Q4 cloud budget?", "2,400", "M6"),
])
def test_paraphrases_are_answered(q, expect, cite):
    c.post("/api/memory/M8/approve", json={"person": "giulia"})
    a = ask("giulia", q)
    assert a["status"] == "answered" and expect in a["text"] and a["citations"][0]["id"] == cite, (q, a)


def test_ambiguous_question_never_gets_the_wrong_fact():
    # Fee fact (M3) and invoice-address fact (M8) each match 3 of 4 words. Offline must not guess.
    for approve in (False, True):
        if approve:
            c.post("/api/memory/M8/approve", json={"person": "giulia"})
        a = ask("giulia", "Where should we send the Atlas milestone 2 invoice?")
        assert a["status"] in ("unknown", "answered")
        if a["status"] == "answered":
            assert a["citations"][0]["id"] == "M8"
        assert "84,000" not in a["text"]


# Failure-hunter regressions ----------------------------------------------------------------------
FINANCE_STRINGS = ("28,000", "84,000", "2,400", "2,050", "ap@verdi", "30 days", "15 days")


def test_sweep_and_event_responses_do_not_leak_traces():
    import json
    blob = json.dumps(c.post("/api/sweep").json()) + json.dumps(c.post("/api/events/nordprint_terms").json())
    for s in FINANCE_STRINGS:
        assert s not in blob, s
    assert '"steps": [' not in blob                      # summaries only


def test_stale_draft_is_withdrawn_when_new_fact_is_approved():
    c.post("/api/events/nordprint_terms")
    alert = [a for a in st("giulia")["alerts"] if a["kind"] == "conflict"][0]
    c.post(f"/api/memory/{alert['candidate_id']}/approve", json={"person": "giulia"})
    p = store.proposals[alert["proposal_id"]]
    assert p["status"] == "withdrawn"
    assert c.post(f"/api/proposals/{p['id']}/approve", json={"person": "giulia"}).status_code == 409
    assert store.outbox == []


def test_draft_survives_if_new_claim_is_rejected():
    c.post("/api/events/nordprint_terms")
    alert = [a for a in st("giulia")["alerts"] if a["kind"] == "conflict"][0]
    c.post(f"/api/memory/{alert['candidate_id']}/reject", json={"person": "giulia"})
    assert store.proposals[alert["proposal_id"]]["status"] == "pending"


@pytest.mark.parametrize("q", ["When does Atlas NOT launch?", "What is the cloud budget for Q4 2027?",
                               "Are NordPrint terms 60 days?", "Who owns Atlas billing and what is the Atlas fee?"])
def test_tricky_questions_get_i_dont_know(q):
    assert ask("giulia", q)["status"] == "unknown", q


def test_clock_never_goes_backwards():
    c.post("/api/events/nordprint_terms")
    c.post("/api/sweep")
    assert store.clock == "2026-12-07T09:20"


def test_ingest_of_all_source_cannot_see_finance_keys():
    from brain import agents, tools as T
    store.processed_sources.add("E1")
    tr = agents.Trace("ingest", "system", "t", ["all"], store.clock)
    keys = T.call(T.Ctx(store, "ingest", "system", None, tr, source_id="E1"), "list_memory_keys", {})["keys"]
    assert {k["key"] for k in keys} == {"atlas.launch_date", "atlas.owners", "office.closure"}


def test_breaker_switches_to_offline(monkeypatch):
    from brain import agents
    monkeypatch.delenv("BRAIN_MODE", raising=False)
    monkeypatch.setattr(agents, "_configured", lambda: object())
    assert agents.client() is not None
    agents.trip_breaker("ConnectError: wifi down")
    try:
        assert agents.client() is None and agents.mode() == "offline"
        assert "paused" in agents.mode_note()
    finally:
        agents.reset_breaker()


# Voice brief (ElevenLabs) ------------------------------------------------------------------------
def test_voice_brief_reads_only_the_persons_own_brief(monkeypatch):
    from brain import voice
    sent = {}
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-not-a-real-key")
    monkeypatch.setattr(voice, "speak", lambda key, text: sent.setdefault(key, text) and b"ID3fake")
    assert c.get("/api/brief/audio", params={"person": "marco"}).status_code == 404   # no brief yet
    c.post("/api/sweep")
    r = c.get("/api/brief/audio", params={"person": "marco"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg"
    text = list(sent.values())[0]
    assert text.startswith("Good morning Marco")
    for s in FINANCE_STRINGS + ("billing", "Billing"):
        assert s not in text, s


def test_voice_brief_without_key_fails_cleanly(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    c.post("/api/sweep")
    r = c.get("/api/brief/audio", params={"person": "giulia"})
    assert r.status_code == 503 and "not configured" in r.json()["detail"]
    assert st("giulia")["voice"] is False


def test_one_slow_call_does_not_take_the_demo_offline(monkeypatch):
    from brain import agents
    monkeypatch.delenv("BRAIN_MODE", raising=False)
    monkeypatch.setattr(agents, "_configured", lambda: object())
    agents.reset_breaker()
    try:
        agents.record_failure("504 DEADLINE_EXCEEDED")
        assert agents.client() is not None                 # still online after one failure
        agents.record_success()
        agents.record_failure("504")
        assert agents.client() is not None                 # success reset the count
        agents.record_failure("504")
        assert agents.client() is None                     # two in a row -> breaker open
    finally:
        agents.reset_breaker()
