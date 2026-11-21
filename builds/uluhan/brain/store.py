"""In-memory state for the demo company. Every read that reaches the model goes through `visible()`.

Demo data only (see app/data/seed.json). State resets from the seed file; nothing is persisted.
"""
from __future__ import annotations

import copy
import json
import threading
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed.json"


def can_see(role: str, audience: list[str]) -> bool:
    return "all" in audience or role in audience


class Store:
    def __init__(self, seed_path: Path = SEED_PATH):
        self.seed_path = seed_path
        self.lock = threading.RLock()
        self.reset()

    # ---- lifecycle -------------------------------------------------------
    def reset(self) -> None:
        with self.lock:
            seed = json.loads(self.seed_path.read_text())
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
            self._n = {"M": len(self.memory), "P": 0, "A": 0, "r": 0}

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

    def visible_memory(self, role: str, statuses=("approved",)) -> list[dict]:
        return [m for m in self.memory.values() if m["status"] in statuses and can_see(role, m["audience"])]

    def visible_sources(self, role: str) -> list[dict]:
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
                    "source_title": src.get("title", ""), "quote": m.get("quote", "")}
        if item_id in self.sources:
            s = self.sources[item_id]
            return {"id": s["id"], "kind": "source", "label": s["title"], "source_id": s["id"],
                    "source_title": s["title"], "quote": ""}
        return None
