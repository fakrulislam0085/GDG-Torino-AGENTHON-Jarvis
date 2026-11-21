"""One annotated Orchard milestone replay. All mutations run under the caller's store lock."""
from email import policy
from email.parser import Parser
from pathlib import Path

from . import tools

MILESTONE = "Orchard / Site acceptance"
KEY = "orchard.acceptance"
REVIEWER = "giulia"
DELIVERY = "orchard-delivery"


def event(name):
    path = Path(__file__).resolve().parents[1] / "billing_examples" / f"{name}.eml"
    mail = Parser(policy=policy.default).parsestr(path.read_text(encoding="utf-8"))
    if mail["X-Milestone"] != MILESTONE:
        raise ValueError("Unexpected milestone in Orchard fixture")
    sid = f"orchard-{name}"
    labels = {"acceptance": "Start Orchard · accepted A+B", "correction": "Customer correction · Site A only",
              "followup": "Ordinary customer follow-up", "duplicate": "Forwarded duplicate acceptance"}
    source = {"id": sid, "type": "mail", "audience": ["finance"], "ts": str(mail["X-Received"]),
              "title": str(mail["Subject"]), "body": mail.get_payload().strip(), "from": str(mail["From"]),
              "to": "giulia@filare.example", "recipient_ids": [REVIEWER], "stage": "live",
              "acceptance_version": int(mail["X-Version"]), "accepted_scope": str(mail["X-Accepted-Scope"])}
    return {"id": sid, "label": "Annotated replay · " + labels[name], "source": source,
            "orchard_fixture": name, "fallback_candidates": []}


def handoff(store, memory, trace):
    scope = store.sources[memory["source_id"]]["accepted_scope"]
    ctx = tools.Ctx(store, "brief", REVIEWER, store.role(REVIEWER), trace)
    result = tools.t_propose_email(ctx, store.people["luca"]["email"], f"Orchard finance handoff · {scope}",
                                   memory["fact"], "Delivery marked site acceptance ready.", [memory["id"], DELIVERY])
    return result["id"]


def receive(store, fixture, src, trace):
    if fixture == "acceptance":
        store.sources[DELIVERY] = {"id": DELIVERY, "title": MILESTONE, "type": "task", "stage": "seed",
                                   "audience": ["finance"], "ts": src["ts"], "body": "Delivery marked site acceptance ready.",
                                   "from": "Delivery", "to": "Finance", "recipient_ids": []}
        store.processed_sources.add(DELIVERY)
        mid = store.next_id("M")
        approved = {"id": mid, "key": KEY, "topic": MILESTONE, "audience": ["finance"], "source_id": src["id"],
                    "fact": src["body"], "quote": src["body"], "status": "approved", "decided_by": REVIEWER,
                    "decided_at": src["ts"], "reviewer_id": REVIEWER}
        store.memory[mid] = approved
        store.log("brain", "memory.imported", mid, "Annotated replay starts with Giulia’s approved A+B decision.", ["finance"])
        handoff(store, approved, trace)
        for name in ("correction", "followup", "duplicate"):
            item = event(name)
            store.live_events[item["id"]] = item
        return

    basis = store.approved_revision({"key": KEY, "audience": ["finance"]})
    original = store.sources[basis["source_id"]]
    if src["acceptance_version"] <= original["acceptance_version"] or src["accepted_scope"] == original["accepted_scope"]:
        trace.guard("Existing scope or old acceptance version. Handoff remains as reviewed.")
        return
    ctx = tools.Ctx(store, "ingest", "system", None, trace, source_id=src["id"])
    result = tools.t_propose_memory(ctx, KEY, MILESTONE, src["body"], src["body"], draft_reply=False)
    candidate = store.memory[result["id"]]
    candidate["reviewer_id"] = REVIEWER
    for draft in store.proposals.values():
        refs = {c["id"] for c in draft["citations"]}
        if draft["status"] == "pending" and {basis["id"], DELIVERY} <= refs:
            draft.update(status="held", hold_candidate=candidate["id"], hold_source=src["id"])
            store.log("brain", "proposal.held", draft["id"], f"Scope correction {src['id']} awaits Giulia.", ["finance"])


def resolve(store, memory, approve, trace):
    for draft in list(store.proposals.values()):
        if draft.get("hold_candidate") != memory["id"] or draft["status"] != "held":
            continue
        original = store.memory[memory["conflicts_with"]]
        if approve or original["status"] != "approved":
            draft.update(status="withdrawn", decided_by=REVIEWER, decided_at=store.clock)
            store.log(REVIEWER, "proposal.withdrawn", draft["id"], "Approved scope changed.", ["finance"])
            if approve:
                handoff(store, memory, trace)
        else:
            draft["status"] = "pending"
            store.log(REVIEWER, "proposal.resumed", draft["id"], "Correction rejected. Original basis retained.", ["finance"])
