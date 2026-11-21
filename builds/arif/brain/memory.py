"""The shared memory people curate. Only 'approved' items are ever used to answer."""
from __future__ import annotations

import itertools
from datetime import datetime

from . import access, audit, store


def approved_for(user_id: str) -> list:
    return [m for m in access.visible(store.memory(), user_id) if m["status"] == "approved"]


def pending_for(user_id: str) -> list:
    return [m for m in access.visible(store.memory(), user_id) if m["status"] == "pending"]


def _set_status(mem_id: str, user_id: str, status: str) -> dict:
    items = store.memory()
    for m in items:
        if m["id"] == mem_id:
            if not access.can_see(m, user_id):
                audit.log("memory_review_denied", user_id, mem_id=mem_id)
                raise PermissionError("You can't review an item you can't see.")
            m["status"] = status
            m["reviewed_by"] = user_id
            m["reviewed_at"] = datetime.now().isoformat(timespec="seconds")
            store.save_memory(items)
            audit.log(f"memory_{status}", user_id, mem_id=mem_id, fact=m["fact"])
            return m
    raise KeyError(mem_id)


def approve(mem_id: str, user_id: str) -> dict:
    return _set_status(mem_id, user_id, "approved")


def reject(mem_id: str, user_id: str) -> dict:
    return _set_status(mem_id, user_id, "rejected")


def add_pending(fact: str, source_ids: list, acl: list, proposed_by: str = "extractor") -> dict:
    """The access list is copied from the source by code. The model never chooses who can see a fact."""
    items = store.memory()
    existing = {m["id"] for m in items}
    new_id = next(f"mem-n{n:02d}" for n in itertools.count(1) if f"mem-n{n:02d}" not in existing)
    item = {"id": new_id, "fact": fact, "sources": source_ids, "acl": list(acl), "status": "pending", "proposed_by": proposed_by}
    items.append(item)
    store.save_memory(items)
    audit.log("memory_proposed", None, mem_id=new_id, fact=fact, sources=source_ids, by=proposed_by)
    return item
