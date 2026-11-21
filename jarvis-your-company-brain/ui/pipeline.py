"""Numbers for the "How your 08:00 email is made" panel on the Morning email page.
Every count goes through access.visible for the signed-in person: nothing they can't see is ever counted."""
from __future__ import annotations

from collections import Counter

from brain import access, guard, memory, phone, store, stripe_sync, zoom
from ui import counts as tally

# The source kinds the brief reads, in the order the panel shows them, with the tool each demo file stands in for.
KINDS = [("email", "Gmail"), ("chat", "Team chat"), ("task", "Task board"), ("doc", "Docs")]
NEXT = ["Google Calendar", "Google Drive", "Slack", "Notion"]


def tool_names() -> dict:
    """kind -> tool name, taken from company.json overview.tools when the tool is listed there."""
    listed = store.company().get("overview", {}).get("tools", []) or []
    return {k: next((t for t in listed if t.lower() == default.lower()), default) for k, default in KINDS}


def source_counts(user: str) -> list:
    """One row per source kind present in the data folder: (kind, tool, items this person may see)."""
    all_kinds = {s["kind"] for s in store.sources()}
    seen = Counter(s["kind"] for s in access.visible(store.sources(), user))
    names = tool_names()
    return [{"kind": k, "tool": names[k], "n": seen.get(k, 0)} for k, _ in KINDS if k in all_kinds]


def guard_blocked(user: str) -> int:
    """Suspicious emails and chat messages this person may see: the brief sets them aside as data (brief.make_brief)."""
    return sum(1 for s in access.visible(store.sources(), user)
               if s["kind"] in ("email", "chat") and guard.suspicious(s["text"]))


def actions_live() -> list:
    """Action tools (they push out, they don't read), each with whether its keys are set."""
    return [{"tool": "Phone call", "via": "ElevenLabs + Twilio", "live": phone.configured()},
            {"tool": "Zoom", "via": "meetings", "live": zoom.configured()},
            {"tool": "Stripe", "via": "revenue sync", "live": stripe_sync.connected()}]


def pipeline(user: str) -> dict:
    srcs = source_counts(user)
    return {"sources": srcs,
            "read": sum(s["n"] for s in srcs),
            "blocked": guard_blocked(user),
            "approved": len(memory.approved_for(user)),
            "waiting": len(memory.pending_for(user)),
            "brief": tally.brief_items(user)}
