"""Replay Orchard through the same workspace endpoints used by the browser."""
import os

from fastapi.testclient import TestClient


def replay(client):
    def receive(name):
        response = client.post(f"/api/events/orchard-{name}")
        response.raise_for_status()
        return response.json()["runs"]

    def state():
        return client.get("/api/state", params={"person": "giulia"}).json()

    def decide(resource, ident, person="giulia"):
        return client.post(f"/api/{resource}/{ident}/approve", json={"person": person}).status_code

    receive("acceptance")
    initial = state()
    original, = [m for m in initial["memory"] if m["source_id"] == "orchard-acceptance"]
    draft, = initial["proposals"]
    assert draft["status"] == "pending" and [c["id"] for c in draft["citations"]] == [original["id"], "orchard-delivery"]
    print("A+B accepted. Pending finance handoff cites original approval and Delivery.")
    for name in ("followup", "duplicate"):
        receive(name)
        assert state()["proposals"][0]["status"] == "pending" and not state()["alerts"]
    receive("correction")
    assert receive("correction") == []
    held = state()
    receipt, = [a["receipt"] for a in held["alerts"]]
    candidate = receipt["claim"]["id"]
    assert receipt["current"]["id"] == original["id"] and receipt["current"]["status"] == "approved"
    assert receipt["claim"]["status"] == "candidate" and receipt["reviewers"] == ["Giulia Ferrero (CFO)"]
    assert held["proposals"][0]["status"] == "held" and decide("proposals", draft["id"]) == 409
    assert not state()["outbox"] and decide("memory", candidate, "elena") == 403
    print("Correction awaiting Giulia. A+B still approved. Old handoff held before release.")
    assert decide("memory", candidate) == 200
    assert decide("memory", candidate) == 409 and decide("proposals", draft["id"]) == 409
    old, fresh = state()["proposals"]
    assert old["status"] == "withdrawn" and fresh["status"] == "pending"
    assert fresh["citations"][0]["id"] == candidate and fresh["citations"][0]["source_id"] == "orchard-correction"
    assert not state()["outbox"] and decide("proposals", fresh["id"], "luca") == 403
    assert decide("proposals", fresh["id"]) == 200 and decide("proposals", fresh["id"]) == 409
    item, = state()["outbox"]
    assert item["proposal_id"] == fresh["id"] and "only site A" in item["body"]
    print("Site A approved. Original blocked. Fresh approval placed one Site A handoff in the mock outbox.")


if __name__ == "__main__":
    os.environ["BRAIN_MODE"] = "offline"
    from brain import server
    with TestClient(server.app) as client:
        replay(client)
