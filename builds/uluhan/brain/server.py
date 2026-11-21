"""HTTP API for the Company Brain (contract: builds/uluhan/API.md). Run:  uvicorn brain.server:app"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from . import env

env.load()   # .env must be read before agents reads GEMINI_MODEL / credentials

from . import agents, voice  # noqa: E402
from .store import Store, can_see

WEB = Path(__file__).resolve().parent.parent / "web"
store = Store()
app = FastAPI(title="Company Brain (demo data)")


class PersonBody(BaseModel):
    person: str


class AskBody(BaseModel):
    person: str
    question: str


def _person(pid: str) -> dict:
    if pid not in store.people:
        raise HTTPException(404, f"unknown person {pid}")
    return store.people[pid]


def _run_summary(r: dict) -> dict:
    return {k: r[k] for k in ("id", "agent", "actor", "trigger", "mode", "model", "status", "started_at", "ms", "usage")} | {
        "steps": len(r["steps"])}


def _visible_run(r: dict, role: str, pid: str) -> bool:
    if r["agent"] == "ask":
        return r["actor"] == pid
    if r["agent"] == "brief":
        return r["actor"] == pid
    return can_see(role, r["audience"])


@app.get("/api/state")
def state(person: str):
    p = _person(person)
    role = p["role"]
    s = store
    with s.lock:
        mem = [m for m in s.memory.values() if can_see(role, m["audience"])]
        props = [x for x in s.proposals.values() if x["owner_role"] == role]
        prop_ids = {x["id"] for x in props}
        return {
            "person": p, "mode": agents.mode(), "mode_note": agents.mode_note(), "voice": voice.enabled(),
            "model": agents.MODEL if agents.mode() == "gemini" else None,
            "clock": s.clock, "company": s.seed["company"],
            "people": list(s.people.values()),
            "brief": s.briefs.get(person),
            "alerts": [a for a in s.alerts if role in a["to_roles"]],
            "memory": [m for m in mem if m["status"] in ("approved", "superseded")],
            "candidates": [m for m in mem if m["status"] == "candidate"],
            "decided_candidates": [m for m in mem if m["status"] == "rejected"],
            "proposals": props,
            "outbox": [o for o in s.outbox if o["proposal_id"] in prop_ids],
            "sources": sorted([x for x in s.sources.values() if can_see(role, x["audience"])],
                              key=lambda x: x["ts"], reverse=True),
            "pending_events": [{"id": e["id"], "label": e["label"]} for e in s.live_events.values()
                               if e["id"] not in s.fired_events],
            "runs": [_run_summary(r) for r in reversed(s.runs) if _visible_run(r, role, person)],
            "audit": [a for a in reversed(s.audit) if can_see(role, a["audience"]) or a["actor"] == person],
        }


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, person: str):
    p = _person(person)
    for r in store.runs:
        if r["id"] == run_id and _visible_run(r, p["role"], person):
            return r
    raise HTTPException(404, "run not found")


# /sweep and /events are not tied to a person, so they return run SUMMARIES only (no steps, no output).
# Full traces go through /api/runs/{id}?person=..., which applies the role filter.
@app.post("/api/sweep")
def sweep():
    return {"runs": [_run_summary(r) for r in agents.sweep(store)]}


@app.post("/api/events/{event_id}")
def event(event_id: str):
    try:
        runs = agents.receive_event(store, event_id)
    except KeyError:
        raise HTTPException(404, "unknown event")
    if runs is None:
        return {"runs": [], "note": "Already received. Replaying the same email changes nothing."}
    return {"runs": [_run_summary(r) for r in runs]}


@app.post("/api/ask")
def ask(body: AskBody):
    _person(body.person)
    run, answer = agents.ask(store, body.person, body.question)
    return {"run": run, "answer": answer}


def _decide_memory(mid: str, pid: str, approve: bool):
    p = _person(pid)
    with store.lock:
        m = store.memory.get(mid)
        if not m:
            raise HTTPException(404, "unknown memory item")
        if not can_see(p["role"], m["audience"]):
            raise HTTPException(403, f"{p['name']} may not curate {', '.join(m['audience'])} memory")
        if m["status"] != "candidate":
            raise HTTPException(409, f"already {m['status']}")
        m["status"] = "approved" if approve else "rejected"
        m["decided_by"], m["decided_at"] = pid, store.clock
        if approve:
            for old in store.memory.values():
                # Only replace items the approver can see; a tech person can never retire a finance fact.
                if (old is not m and old["status"] == "approved" and old["key"] == m["key"]
                        and can_see(p["role"], old["audience"])):
                    old["status"], old["superseded_by"] = "superseded", m["id"]
                    store.log(pid, "memory.superseded", old["id"], f"replaced by {m['id']}", old["audience"])
        for a in store.alerts:
            if a.get("candidate_id") == mid:
                a["closed"] = True
                # The drafted "please send the signed amendment" reply quotes the OLD fact. Once the new fact is
                # accepted it is stale, so it must not be sendable any more.
                pr = store.proposals.get(a.get("proposal_id") or "")
                if approve and pr and pr["status"] == "pending":
                    pr["status"], pr["decided_by"], pr["decided_at"] = "withdrawn", "brain", store.clock
                    store.log("brain", "proposal.withdrawn", pr["id"], f"stale after {mid} was approved",
                              [pr["owner_role"]])
        store.log(pid, "memory.approved" if approve else "memory.rejected", mid, f"{m['topic']}: {m['fact']}",
                  m["audience"])
        return {"memory": m}


@app.post("/api/memory/{mid}/approve")
def approve_memory(mid: str, body: PersonBody):
    return _decide_memory(mid, body.person, True)


@app.post("/api/memory/{mid}/reject")
def reject_memory(mid: str, body: PersonBody):
    return _decide_memory(mid, body.person, False)


def _decide_proposal(pid_: str, person: str, approve: bool):
    p = _person(person)
    with store.lock:
        pr = store.proposals.get(pid_)
        if not pr:
            raise HTTPException(404, "unknown proposal")
        if pr["owner_role"] != p["role"]:
            raise HTTPException(403, f"only {pr['owner_role']} can decide this proposal")
        if pr["status"] != "pending":
            raise HTTPException(409, f"already {pr['status']}")
        pr["status"] = "approved" if approve else "rejected"
        pr["decided_by"], pr["decided_at"] = person, store.clock
        out = None
        if approve:
            out = {"id": f"O{len(store.outbox) + 1}", "proposal_id": pr["id"], "to": pr["to"], "subject": pr["subject"],
                   "body": pr["body"], "approved_by": person, "at": store.clock,
                   "note": "Mock outbox: nothing leaves this demo."}
            store.outbox.append(out)
        store.log(person, "proposal.approved" if approve else "proposal.rejected", pr["id"],
                  f"email to {pr['to']}: {pr['subject']}", [pr["owner_role"]])
        return {"proposal": pr, "outbox_item": out}


@app.post("/api/proposals/{pid_}/approve")
def approve_proposal(pid_: str, body: PersonBody):
    return _decide_proposal(pid_, body.person, True)


@app.post("/api/proposals/{pid_}/reject")
def reject_proposal(pid_: str, body: PersonBody):
    return _decide_proposal(pid_, body.person, False)


@app.get("/api/brief/audio")
def brief_audio(person: str):
    """The person's own brief, read aloud by ElevenLabs. Only text this person already sees is sent."""
    p = _person(person)
    b = store.briefs.get(person)
    if not b:
        raise HTTPException(404, "no brief yet")
    if not voice.enabled():
        raise HTTPException(503, "ElevenLabs is not configured (ELEVENLABS_API_KEY)")
    text = voice.script(p, b)
    try:
        audio = voice.speak(b["run_id"], text)
    except Exception as e:
        raise HTTPException(502, f"voice failed: {str(e)[:160]}")
    store.log("brain", "voice.brief", b["run_id"], f"read {len(text)} chars aloud for {p['name']}", [p["role"]])
    return Response(audio, media_type="audio/mpeg")


@app.post("/api/reset")
def reset():
    store.reset()
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")
