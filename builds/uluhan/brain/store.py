"""In-memory state for the demo company. Every read that reaches the model goes through `visible()`.

Demo data comes from the team's shared data directory. State resets from the seed file; nothing is persisted.
"""
from __future__ import annotations

import copy
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from .shared import load_shared

# Job titles that carry authority over their team's facts (from the org chart).
LEAD_TITLE = re.compile(r"\b(CEO|CFO|CTO|COO|lead|head|director)\b", re.I)


def can_see(role: str | list[str], audience: list[str]) -> bool:
    groups = {role} if isinstance(role, str) else set(role)
    return "all" in audience or "exec" in groups or bool(groups.intersection(audience))


def same_audience(first: list[str], second: list[str]) -> bool:
    return set(first) == set(second)


class Store:
    def __init__(self, seed_path: Path | None = None):
        self.seed_path = seed_path
        self.lock = threading.RLock()
        self.agent_operation = threading.Lock()
        self.reset()

    # ---- lifecycle -------------------------------------------------------
    def reset(self) -> None:
        with self.lock:
            seed = json.loads(self.seed_path.read_text()) if self.seed_path else load_shared()
            self.seed = seed
            self.people = {p["id"]: p for p in seed["people"]}
            self.sources = {s["id"]: dict(s) for s in seed["sources"]}
            self.memory = {}
            for m in seed["memory"]:
                m = {"conflicts_with": None, "superseded_by": None, "decided_by": None, "decided_at": None, **m}
                self.memory[m["id"]] = m
            self.live_events = {e["id"]: e for e in seed["live_events"]}
            self.fallback_candidates = copy.deepcopy(seed.get("fallback_candidates", {}))
            for e in seed["live_events"]:
                self.fallback_candidates[e["source"]["id"]] = e["fallback_candidates"]
            self.clock = seed["clock_start"]
            self.proposals: dict[str, dict] = {}
            self.alerts: list[dict] = []
            self.outbox: list[dict] = []
            self.briefs: dict[str, dict] = {}
            self.runs: list[dict] = []
            self.audit: list[dict] = []
            self.processed_sources: set[str] = {s["id"] for s in seed["sources"] if s.get("stage") == "seed"}
            self.fired_events: set[str] = set()
            self._n = {"M": max((int(m[1:]) for m in self.memory if m.startswith("M") and m[1:].isdigit()), default=0), "P": 0, "A": 0, "r": 0}

    def next_id(self, prefix: str) -> str:
        with self.lock:
            self._n[prefix] += 1
            return f"{prefix}{self._n[prefix]}"

    # ---- people / access -------------------------------------------------
    def person(self, person_id: str) -> dict:
        if person_id not in self.people:
            raise KeyError(person_id)
        return self.people[person_id]

    def role(self, person_id: str) -> str:
        return self.person(person_id)["role"]

    def access(self, person_id: str) -> list[str]:
        person = self.person(person_id)
        return person.get("groups", [person["role"]])

    def may_decide_proposal(self, person_id: str, proposal: dict) -> bool:
        owner = proposal.get("owner_id")
        return owner == person_id if owner else proposal["owner_role"] in self.access(person_id)

    def replays_current_evidence(self, candidate: dict) -> bool:
        def timestamp(memory):
            stamp = datetime.fromisoformat(self.sources[memory["source_id"]]["ts"])
            return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)

        return any(
            old["key"] == candidate["key"] and same_audience(old["audience"], candidate["audience"])
            and old["status"] == "approved" and timestamp(candidate) < timestamp(old)
            for old in self.memory.values()
        )

    # ---- change control -------------------------------------------------
    def fact_reviewers(self, fact: dict) -> list[dict] | None:
        """Who may replace an approved fact: whoever approved it, a lead of a team that owns it, or exec.
        Being newer never makes a message authoritative. None = no approver on record (any curator may decide)."""
        if not fact.get("decided_by") or fact["decided_by"] not in self.people:
            return None
        owners = set(fact["audience"]) - {"all"}
        out = []
        for p in self.people.values():
            groups = set(p.get("groups", [p.get("role")]))
            if (p["id"] == fact["decided_by"] or "exec" in groups
                    or (groups & owners and LEAD_TITLE.search(p.get("title", "")))):
                out.append(p)
        return out

    def may_revise(self, person_id: str, fact: dict) -> bool:
        reviewers = self.fact_reviewers(fact)
        return reviewers is None or any(p["id"] == person_id for p in reviewers)

    def decision_receipt(self, alert: dict, person_id: str) -> dict | None:
        """A human-readable record of why a shared fact did or did not change. Built only from the alert, the two
        memory items, their sources and the audit trail; nothing new is stored."""
        old, new = self.memory.get(alert.get("memory_id") or ""), self.memory.get(alert.get("candidate_id") or "")
        if not old or not new:
            return None

        def sources(m):
            out = []
            for sid in m.get("source_ids", [m["source_id"]]):
                src = self.sources.get(sid)
                if src:
                    out.append({"id": sid, "source_id": sid, "label": src["title"], "date": src["ts"][:10],
                                "from": src.get("from", "")})
            return out

        def who(pid):
            p = self.people.get(pid or "")
            return f"{p['name']} ({p.get('title', p.get('role', ''))})" if p else (pid or "nobody")

        stale = bool(new.get("stale_evidence")) or self.replays_current_evidence(new)
        reviewers = self.fact_reviewers(old)
        old_date, new_src = (old.get("decided_at") or "")[:10], sources(new)
        new_date = new_src[0]["date"] if new_src else ""
        reasons = ["An incoming message is a claim, not a decision. It was filed as a candidate and never "
                   "written over the approved fact."]
        if stale:
            reasons.append(f"Older evidence: the claim is dated {new_date}, the approved decision {old_date}. "
                           "Older evidence cannot replace a newer decision.")
        if reviewers:
            reasons.append("Being newer would not be enough either: only " + ", ".join(who(p["id"]) for p in reviewers)
                           + " can change an approved fact.")
        replaced_by_claim = old.get("superseded_by") == new["id"] and new["status"] in ("approved", "superseded")
        if new["status"] == "rejected":
            outcome = f"Claim rejected by {who(new.get('decided_by'))}. Company record unchanged by this claim."
        elif replaced_by_claim:
            outcome = f"Record replaced after review by {who(new.get('decided_by'))}."
        elif new["status"] == "candidate":
            outcome = "Awaiting a decision. Company record unchanged."
        else:
            outcome = "This claim did not replace the referenced record."
        return {
            "current": {"id": old["id"], "fact": old["fact"], "status": old["status"], "approved_by": who(old.get("decided_by")),
                        "approved_on": old_date, "sources": sources(old)},
            "claim": {"id": new["id"], "fact": new["fact"], "status": new["status"], "dated": new_date,
                      "sources": new_src},
            "reasons": reasons,
            "reviewers": [who(p["id"]) for p in reviewers] if reviewers else ["anyone who can see this fact"],
            "record_changed": replaced_by_claim,
            "outcome": outcome,
            "you_can_approve": (new["status"] == "candidate" and not stale and self.may_revise(person_id, old)),
            "you_can_reject": new["status"] == "candidate",
        }

    def visible_memory(self, role: str | list[str], statuses=("approved",)) -> list[dict]:
        return [m for m in self.memory.values() if m["status"] in statuses and can_see(role, m["audience"])]

    def visible_sources(self, role: str | list[str]) -> list[dict]:
        return [s for s in self.sources.values() if can_see(role, s["audience"])]

    # ---- audit -----------------------------------------------------------
    def log(self, actor: str, action: str, target: str, detail: str, audience: list[str] | None = None) -> None:
        with self.lock:
            self.audit.append({
                "i": len(self.audit) + 1, "clock": self.clock, "actor": actor, "action": action,
                "target": target, "detail": detail, "audience": audience or ["all"],
            })

    def citation(self, item_id: str) -> dict | None:
        if item_id in self.memory:
            m = self.memory[item_id]
            src = self.sources.get(m["source_id"], {})
            return {"id": m["id"], "kind": "memory", "label": m["topic"], "source_id": m["source_id"],
                    "source_title": src.get("title", ""), "quote": m.get("quote", ""), "fact": m["fact"]}
        if item_id in self.sources:
            s = self.sources[item_id]
            return {"id": s["id"], "kind": "source", "label": s["title"], "source_id": s["id"],
                    "source_title": s["title"], "quote": ""}
        return None
