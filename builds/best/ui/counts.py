"""Counts for the Today header and the sidebar nav badges, and the one-tap question chips.
Every count uses the same role filter as the page it points to: nothing a person can't see is ever counted."""
from __future__ import annotations

from brain import memory, propose, store


def brief_items(user: str) -> int:
    """This person's brief: the 08:00 items plus anything new since (the same rows the Today page shows)."""
    b = store.briefs().get(user, {})
    return len(b.get("alerts", [])) + len(b.get("items", []))


def to_review(user: str) -> int:
    """Pending memory this person can see AND may decide on (the Approve/Reject buttons on the Memory page)."""
    return sum(memory.can_review(m["id"], user) for m in memory.pending_for(user))


def pending_actions(user: str) -> int:
    """Drafts proposed to this person and waiting for their approval (the Approvals page header filter)."""
    return sum(a["status"] == "awaiting_approval" for a in propose.for_user(user))


def counts(user: str) -> dict:
    return {"brief": brief_items(user), "review": to_review(user), "actions": pending_actions(user)}


def chip_questions(demo: dict, limit: int = 4) -> list:
    """Questions for the one-tap chips: the jury checklist questions (non-empty, de-duplicated, in order), then the
    ask placeholder. Case and punctuation don't make a new chip."""
    out, seen = [], set()
    for q in [c.get("question", "") for c in demo.get("checks", [])] + [demo.get("ask_placeholder", "")]:
        q = " ".join(str(q or "").split())
        k = "".join(ch for ch in q.lower() if ch.isalnum())
        if q and k not in seen:
            seen.add(k)
            out.append(q)
    return out[:limit]
