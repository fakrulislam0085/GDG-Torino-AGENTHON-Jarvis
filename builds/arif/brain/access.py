"""Who can see what. Enforced in code, before any model call. Identity comes from the session, never from the text."""
from __future__ import annotations

from . import store


def groups(user_id: str) -> list:
    person = store.people().get(user_id)
    if person is None:
        raise ValueError(f"unknown user {user_id!r}")
    return person["groups"]


def can_see(item: dict, user_id: str) -> bool:
    g = groups(user_id)
    acl = item.get("acl", [])
    return "exec" in g or "all" in acl or any(a in g for a in acl)


def can_approve(item: dict, user_id: str) -> bool:
    """Who may approve, reject, edit or replace a fact: the CEO (exec) always; otherwise you must see it AND hold the
    owning role for every owned group in its access list (finance -> CFO, tech -> CTO, marketing -> Social Media)."""
    if not can_see(item, user_id):
        return False
    if "exec" in groups(user_id):
        return True
    if "all" in item.get("acl", []):   # a company-wide fact: only the CEO decides
        return False
    owners = store.company().get("approvers", {})
    role = store.people()[user_id]["role"]
    return all(role in owners[g] for g in item.get("acl", []) if g in owners)


def visible(items: list, user_id: str) -> list:
    return [i for i in items if can_see(i, user_id)]
