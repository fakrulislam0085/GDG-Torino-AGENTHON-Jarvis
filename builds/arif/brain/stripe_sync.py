"""Stripe -> Jarvis -> Notion. Reads payments, works out revenue per course, and PROPOSES:
- a pending finance fact (flagged if it contradicts what Notion says, e.g. the old revenue figure)
- a Notion page update that waits in Approvals.
Only the CFO or the CEO can run it, approve the fact, or approve the Notion write. Nothing is written by itself.

Source: STRIPE_API_KEY (a restricted, read-only TEST-mode key) -> api.stripe.com/v1/charges.
Without it: the demo export in data_poliprep/stripe_charges.json (same object format, invented data).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import requests

from . import access, audit, memory, propose, store

NOTION_PAGE = "notion-002"   # "Notion · Cost analysis, Cohort 1"


def _charges() -> tuple[list, str]:
    key = os.getenv("STRIPE_API_KEY", "")
    if key.startswith(("rk_test_", "sk_test_")):
        r = requests.get("https://api.stripe.com/v1/charges", params={"limit": 100}, auth=(key, ""), timeout=20)
        r.raise_for_status()
        return r.json().get("data", []), "Stripe (live API, test mode)"
    data = store._read(store.DATA / "stripe_charges.json", {"data": []})
    return data.get("data", []), "Stripe (demo export)"


def summarise(charges: list) -> dict:
    by = {}
    for ch in charges:
        if ch.get("status") != "succeeded":
            continue
        prod = (ch.get("metadata") or {}).get("product", "other")
        s = by.setdefault(prod, {"payments": 0, "gross": 0, "refunds": 0, "refunded_count": 0})
        s["payments"] += 1
        s["gross"] += ch.get("amount", 0)
        if ch.get("amount_refunded"):
            s["refunds"] += ch["amount_refunded"]
            s["refunded_count"] += 1
    for s in by.values():
        s["net"] = s["gross"] - s["refunds"]
    failed = sum(1 for ch in charges if ch.get("status") == "failed")
    total = {"payments": sum(s["payments"] for s in by.values()), "net": sum(s["net"] for s in by.values()),
             "refunded_count": sum(s["refunded_count"] for s in by.values()), "failed": failed}
    return {"by_product": by, "total": total}


def _eur(cents: int) -> str:
    return f"\u20ac{cents / 100:,.0f}"


def sync(user_id: str) -> dict:
    groups = access.groups(user_id)
    if not ("exec" in groups or store.people()[user_id]["role"] == "CFO"):
        audit.log("stripe_sync_denied", user_id)
        raise PermissionError("Only the CFO or the CEO can sync Stripe (it is finance data).")
    charges, origin = _charges()
    s = summarise(charges)
    t = s["total"]
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    names = {a["id"]: a["name"] for a in store.audiences().values()}
    lines = [f"{names.get(p, p).replace(' students', '')}: {v['payments']} payments, net {_eur(v['net'])}"
             + (f" after {v['refunded_count']} refund" if v["refunded_count"] else "")
             for p, v in sorted(s["by_product"].items())]
    text = (f"{origin}, {today}: {t['payments']} successful payments, {t['refunded_count']} refunded, "
            f"{t['failed']} failed. Net Cohort 1 revenue {_eur(t['net'])}. " + "; ".join(lines) + ".")
    syncs = store._read(store.STATE / "stripe_syncs.json", [])
    sid = f"stripe-{len(syncs) + 1:03d}"
    syncs.append({"id": sid, "title": f"Stripe sync ({origin})", "text": text, "acl": ["finance"],
                  "date": datetime.now().isoformat(timespec="seconds"), "author": "stripe", "summary": s})
    store._write(store.STATE / "stripe_syncs.json", syncs)
    fact = f"Cohort 1 revenue so far is {_eur(t['net'])} net ({t['payments']} payments, {t['refunded_count']} refund), from Stripe on {today}."
    pending = memory.add_pending(fact, [sid], ["finance"], proposed_by="stripe-sync")
    conflicts = memory.conflicts(pending["id"], user_id)
    body = ("Update the Notion page 'Cost analysis, Cohort 1':\n"
            + "\n".join(f"- {line}" for line in lines)
            + f"\n- Total net revenue: {_eur(t['net'])} (source: {origin}, {today})")
    action = propose.add(user_id, "notion_update", NOTION_PAGE, "Update Notion: Cohort 1 revenue from Stripe", body,
                         f"Stripe sync {sid}", [sid, NOTION_PAGE])
    audit.log("stripe_synced", user_id, sync=sid, origin=origin, net=t["net"], payments=t["payments"],
              pending=pending["id"], conflicts=[c["id"] for c in conflicts], action=action["id"] if action else None)
    return {"sync": sid, "origin": origin, "summary": s, "pending": pending["id"], "conflicts": conflicts,
            "action": action["id"] if action else None, "text": text}
