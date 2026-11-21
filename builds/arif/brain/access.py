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


def visible(items: list, user_id: str) -> list:
    return [i for i in items if can_see(i, user_id)]
