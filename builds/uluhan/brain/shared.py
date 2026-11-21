"""Translate the team's shared Filare fixtures into the existing store contract."""
from datetime import datetime
import json
from pathlib import Path

SHARED_ROOT = Path(__file__).resolve().parents[3] / "data"

# Presentation and lookup labels for authoritative shared memory, without duplicating facts.
MEMORY_LABELS = {
    "mem-001": ("cloud.budget.q1.2027", "Q1 2027 cloud budget"),
    "mem-002": ("finance.runway", "Cash runway and net burn"),
    "mem-003": ("langhe.outage", "Langhe Viva outage and renewal risk"),
    "mem-004": ("gateway.firmware.bug", "Gateway firmware 2.2 restart issue"),
    "mem-005": ("sensorparts.invoice", "SensorParts invoice due date and amount"),
    "mem-006": ("november.payroll", "November payroll deadline"),
    "mem-007": ("hiring.backend.budget", "Senior backend hire budget"),
    "mem-008": ("gateway.shipping.policy", "New-gateway firmware and update policy"),
    "mem-009": ("team.lunch", "Team lunch"),
    "mem-010": ("support.response", "Support response and outage visit deadlines"),
    "mem-p01": ("langhe.fix.rollout", "Langhe fix rollout schedule"),
    "mem-p02": ("langhe.contract.value", "Langhe Viva contract value"),
}

LIVE_EMAILS = {
    "email-006": "Archived cloud budget email",
    "email-008": "Suspicious email to Sara",
}


def load_shared():
    def read(name):
        return json.loads((SHARED_ROOT / name).read_text(encoding="utf-8"))

    company = read("company.json")
    people = [
        {**p, "title": p["role"], "role": next(g for g in p["groups"] if g != "all"),
         "email": f"{p['id']}@filare.example"}
        for p in company["people"]
    ]
    directory = {p["id"]: p["email"] for p in people}
    sweep_time = company["company"]["demo_now"]

    def source(record, kind, sender, recipients, title, body, stamp):
        return {
            "id": record["id"], "type": kind, "audience": record["acl"], "ts": stamp,
            "stage": "overnight" if kind == "mail" else "seed", "from": directory.get(sender, sender),
            "to": ", ".join(directory.get(person, person) for person in recipients), "recipient_ids": recipients,
            "title": title, "body": body,
        }

    emails = {
        e["id"]: source(e, "mail", e["from"], e["to"] + e.get("cc", []), e["subject"], e["body"], e["date"])
        for e in read("emails.json")
    }
    sources = dict(emails)
    for chat in read("chat.json"):
        sources[chat["id"]] = source(
            chat, "chat", chat["author"], [], chat["channel"], chat["text"], chat["date"],
        )
    for task in read("tasks.json"):
        detail = f"{task['title']}. Status: {task['status']}. Due {task['due']}."
        if task.get("blocked_by"):
            detail += f" Blocked by {task['blocked_by']}."
        sources[task["id"]] = source(task, "task", task["owner"], [task["owner"]], task["title"], detail, sweep_time)
    for path in sorted((SHARED_ROOT / "docs").glob("*.md")):
        _, front, body = path.read_text(encoding="utf-8").split("---", 2)
        fields = dict(line.split(": ", 1) for line in front.strip().splitlines())
        fields["acl"] = [g.strip() for g in fields["acl"].strip("[]").split(",")]
        sources[fields["id"]] = source(fields, "doc", "Filare Labs", [], fields["title"], body.strip(), fields["updated"])

    memory = []
    for item in read("memory_seed.json"):
        primary = sources[item["sources"][0]]
        key, topic = MEMORY_LABELS[item["id"]]
        memory.append({
            "id": item["id"], "key": key, "topic": topic, "fact": item["fact"],
            "audience": item["acl"], "source_id": primary["id"], "source_ids": item["sources"],
            "quote": primary["body"], "status": "candidate" if item["status"] == "pending" else item["status"],
            "decided_by": item.get("approved_by"), "decided_at": primary["ts"] if item.get("approved_by") else None,
        })

    live_events = []
    for eid, label in LIVE_EMAILS.items():
        src = sources.pop(eid)
        live_events.append({"id": eid, "label": label, "source": src, "fallback_candidates": []})
    archived_email = emails["email-006"]
    live_events[0]["fallback_candidates"].append({
        "key": "cloud.budget.q1.2027", "topic": "Q1 2027 cloud budget",
        "fact": archived_email["body"], "quote": archived_email["body"],
    })
    return {
        "company": company["company"]["name"], "people": people, "memory": memory,
        "sources": list(sources.values()), "live_events": live_events,
        "clock_start": datetime.fromisoformat(sweep_time).replace(hour=8, minute=25).isoformat(),
        "sweep_time": sweep_time, "sweep_label": sweep_time[11:16],
    }
