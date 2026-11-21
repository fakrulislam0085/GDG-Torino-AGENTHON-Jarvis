"""Stripe -> Jarvis -> the revenue page. Reads subscription payments, works out revenue per plan, and PROPOSES:
- a pending finance fact (flagged if it contradicts approved memory, e.g. the older figure in the revenue tracker)
- an update to the team's revenue page (company.json -> stripe.page) that waits in Approvals.
Only the CFO or the CEO can run it, approve the fact, or approve the page update. Nothing is written by itself.

Source: STRIPE_API_KEY (a restricted, read-only TEST-mode key) -> api.stripe.com/v1/charges.
Without it: the demo export stripe_charges.json in the active data folder (same object format, invented customers).
A company without either (or without a stripe.page in company.json) is "not connected": the button hides, sync refuses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import requests

from . import access, audit, memory, propose, store


def config() -> dict:
    return store.company().get("stripe", {})


def page_id() -> str:
    """The doc or Notion page the sync proposes to update (configurable, e.g. 'doc-004')."""
    return config().get("page", "")


def connected() -> bool:
    """Stripe is set up for this company: a target page in company.json, and a test key or the demo export file."""
    key = os.getenv("STRIPE_API_KEY", "")
    return bool(page_id()) and (key.startswith(("rk_test_", "sk_test_")) or (store.DATA / "stripe_charges.json").exists())


def can_sync(user_id: str) -> bool:
    """The CEO (exec) or a finance role named in company.json (stripe.roles, default CFO)."""
    person = store.people().get(user_id)
    if person is None:
        return False
    return "exec" in person["groups"] or person["role"] in config().get("roles", ["CFO"])


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
    return f"€{cents / 100:,.0f}"


def sync(user_id: str) -> dict:
    if not can_sync(user_id):
        audit.log("stripe_sync_denied", user_id)
        raise PermissionError("Only the CFO or the CEO can sync Stripe (it is finance data).")
    if not connected():
        raise RuntimeError("Stripe is not connected for this company.")
    charges, origin = _charges()
    s = summarise(charges)
    t = s["total"]
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    names = config().get("products", {})
    topic = config().get("topic", "Subscription revenue collected")
    lines = [f"{names.get(p, p)}: {v['payments']} payments, {_eur(v['net'])} after refunds"
             + (f" ({v['refunded_count']} refunded)" if v["refunded_count"] else "")
             for p, v in sorted(s["by_product"].items())]
    fact = (f"{topic} so far is {_eur(t['net'])} after refunds ({t['payments']} payments, {t['refunded_count']} refunded), "
            f"from Stripe on {today}.")
    text = (f"{origin}, {today}: {t['payments']} successful payments, {t['refunded_count']} refunded, "
            f"{t['failed']} failed. " + "; ".join(lines) + f". {fact}")
    syncs = store._read(store.STATE / "stripe_syncs.json", [])
    sid = f"stripe-{len(syncs) + 1:03d}"
    syncs.append({"id": sid, "title": f"Stripe sync ({origin})", "text": text, "acl": ["finance"],
                  "date": datetime.now().isoformat(timespec="seconds"), "author": "stripe", "summary": s})
    store._write(store.STATE / "stripe_syncs.json", syncs)
    pending = memory.add_pending(fact, [sid], ["finance"], proposed_by="stripe-sync")
    conflicts = memory.conflicts(pending["id"], user_id)
    page = page_id()
    title = store.label(page) if page else "the revenue page"
    body = (f"Update the page '{title}':\n"
            + "\n".join(f"- {line}" for line in lines)
            + f"\n- Total collected after refunds: {_eur(t['net'])}, {t['failed']} failed payment to chase"
            + f" (source: {origin}, {today})")
    action = None
    if page:
        action = propose.add(user_id, "notion_update", page, f"Update '{title}' from Stripe", body,
                             f"Stripe sync {sid}", [sid, page])
    audit.log("stripe_synced", user_id, sync=sid, origin=origin, net=t["net"], payments=t["payments"],
              pending=pending["id"], conflicts=[c["id"] for c in conflicts], action=action["id"] if action else None)
    return {"sync": sid, "origin": origin, "summary": s, "pending": pending["id"], "conflicts": conflicts,
            "action": action["id"] if action else None, "text": text}
