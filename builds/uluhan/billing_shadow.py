"""Isolated synthetic shadow run. Run from builds/uluhan with the existing environment."""
from email import policy
from email.parser import Parser
import os

os.environ["BRAIN_MODE"] = "offline"
from fastapi.testclient import TestClient
from brain import server, tools
from brain.agents import Trace

MILESTONE = "Orchard / Site acceptance"


def ingest_copy(store, raw, sid):
    """A coordinator forwards a copy and explicitly records milestone, version and accepted scope."""
    mail = Parser(policy=policy.default).parsestr(raw)
    assert mail["X-Milestone"] == MILESTONE
    scope = mail["X-Accepted-Scope"]
    store.sources[sid] = dict(id=sid, type="mail", audience=["finance"], ts=mail["X-Received"],
                              title=mail["Subject"], body=mail.get_payload().strip(),
                              stage="live", **{"from": mail["From"], "to": "giulia@filare.example"})
    return int(mail["X-Version"]), scope


def main():
    # This command owns its in-memory application instance. No external service or mail transport.
    store = server.store
    client = TestClient(server.app)
    reviewer = "giulia"
    def decide(resource, ident, who=reviewer):
        return client.post(f"/api/{resource}/{ident}/approve", json={"person": who}).status_code

    def candidate(sid):
        ctx = tools.Ctx(store, "ingest", "system", None, Trace("ingest", "system", sid, ["finance"], store.clock), source_id=sid)
        fact = store.sources[sid]["body"]
        return tools.t_propose_memory(ctx, "orchard.acceptance", MILESTONE, fact, fact)["id"]

    def handoff(mid):
        ctx = tools.Ctx(store, "brief", reviewer, store.role(reviewer), Trace("brief", reviewer, MILESTONE, ["finance"], store.clock))
        return tools.t_propose_email(ctx, "luca@filare.example", "Finance handoff · Orchard",
                                     store.memory[mid]["fact"], "Delivery marked the milestone ready.",
                                     [mid, "orchard-delivery"])["id"]

    store.sources["orchard-delivery"] = dict(id="orchard-delivery", title=MILESTONE, type="task", stage="live",
        audience=["finance"], ts=store.clock, body="Delivery marked site acceptance ready.", **{"from":"Delivery","to":"Finance"})
    from pathlib import Path
    folder = Path(__file__).parent / "billing_examples"
    version, accepted = ingest_copy(store, (folder / "acceptance.eml").read_text(), "acceptance-v1")
    original = candidate("acceptance-v1")
    assert decide("memory", original) == 200
    pending = handoff(original)
    print("Delivery ready. Giulia approved acceptance-v1. Pending handoff", pending)
    for filename in ("followup", "duplicate", "correction"):
        revision, scope = ingest_copy(store, (folder / f"{filename}.eml").read_text(), filename)
        if revision <= version or scope == accepted:
            print(filename, "retained as evidence; no hold")
            assert store.proposals[pending]["status"] == "pending"
            continue
        with store.lock:
            revised = candidate(filename)
            draft = store.proposals[pending]
            draft.update(status="withdrawn", decided_by="brain", decided_at=store.clock)
            store.log("brain", "proposal.withdrawn", pending, f"{filename} changed scope; {reviewer} reviews {revised}", ["finance"])
        assert store.memory[original]["status"] == "approved" and store.memory[revised]["status"] == "candidate"
        assert decide("proposals", pending) == 409 and not store.outbox
        print("Held before approval. Original evidence still approved. Giulia reviews correction.")
        assert decide("memory", revised) == 200
        fresh = handoff(revised)
        assert fresh != pending and store.proposals[fresh]["citations"][0]["id"] == revised
        assert decide("proposals", fresh, "luca") == 403
        assert decide("proposals", fresh) == 200 and decide("proposals", fresh) == 409
        assert len(store.outbox) == 1
        print("Fresh handoff approved by Giulia against correction. One mock entry.")


if __name__ == "__main__":
    main()
