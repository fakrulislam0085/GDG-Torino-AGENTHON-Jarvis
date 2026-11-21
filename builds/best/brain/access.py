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
    """Who may approve, reject, edit or replace a fact (rules in company.json: approvers, strict_approvers):
    - the CEO (exec) always, and only the CEO for a company-wide fact (acl "all");
    - otherwise you must see it AND hold an approver role for at least one team it belongs to;
    - a "strict" team (finance) must always sign: a fact that touches money needs the CFO, even when shared with tech."""
    if not can_see(item, user_id):
        return False
    if "exec" in groups(user_id):
        return True
    acl = item.get("acl", [])
    if "all" in acl:   # a company-wide fact: only the CEO decides
        return False
    owners = store.company().get("approvers", {})
    strict = set(store.company().get("strict_approvers", []))
    role = store.people()[user_id]["role"]
    owned = [g for g in acl if g in owners]
    if not owned:
        return False
    if any(role not in owners[g] for g in owned if g in strict):
        return False
    return any(role in owners[g] for g in owned)


def approver_roles(item: dict) -> list:
    """The roles that may decide on this fact, in words, for the 'only X can decide' messages."""
    if "all" in item.get("acl", []):
        return ["CEO"]
    owners = store.company().get("approvers", {})
    strict = [g for g in item.get("acl", []) if g in store.company().get("strict_approvers", []) and g in owners]
    groups_ = strict or [g for g in item.get("acl", []) if g in owners]
    return sorted({r for g in groups_ for r in owners[g]}) + ["CEO"]


def visible(items: list, user_id: str) -> list:
    return [i for i in items if can_see(i, user_id)]
