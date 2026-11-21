"""Company data (builds/arif/data_poliprep/ by default; BRAIN_DATA=filare uses the repo-root fake company) + runtime state."""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import uuid
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
REPO = BUILD.parents[1]
DATA = REPO / "data" if os.getenv("BRAIN_DATA", "poliprep") == "filare" else BUILD / "data_poliprep"
STATE = Path(os.getenv("BRAIN_STATE_DIR", BUILD / "state"))


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


_LOCK = threading.Lock()


def _write(path: Path, value) -> None:
    with _LOCK:
        STATE.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.stem}.{uuid.uuid4().hex}.tmp")
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


def _clean(item: dict) -> dict:
    """Drop the '_demo' notes we wrote for humans: the model never sees them."""
    return {k: v for k, v in item.items() if not k.startswith("_")}


# ---------- the company ----------
def company() -> dict:
    return _read(DATA / "company.json", {})


def people() -> dict:
    """App users (they log in, they have groups)."""
    return {p["id"]: p for p in company().get("people", [])}


def team() -> dict:
    """Users + contacts (e.g. tutors): anyone Jarvis may draft a message to."""
    out = {c["id"]: c for c in company().get("contacts", [])}
    out.update(people())
    return out


def company_name() -> str:
    return company().get("company", {}).get("name", "the company")


def demo_events() -> dict:
    return _read(DATA / "demo_events.json", {})


def _docs() -> list:
    out = []
    for f in sorted((DATA / "docs").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
        if not m:
            continue
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        acl = [a.strip() for a in meta.get("acl", "[]").strip("[]").split(",") if a.strip()]
        out.append({"id": meta["id"], "kind": "notion" if meta["id"].startswith("notion") else "doc", "title": meta.get("title", f.stem),
                    "date": meta.get("updated", ""), "text": m.group(2).strip(), "acl": acl})
    return out


def sources() -> list:
    """Every source item (email, chat, task, doc) in one shape: id, kind, title, text, acl, date, author."""
    items = []
    for e in _read(DATA / "emails.json", []) + incoming():
        e = _clean(e)
        items.append({"id": e["id"], "kind": "email", "title": e["subject"], "text": e["body"], "acl": e["acl"],
                      "date": e["date"], "author": e["from"], "to": e.get("to", [])})
    for c in _read(DATA / "chat.json", []):
        c = _clean(c)
        items.append({"id": c["id"], "kind": "chat", "title": c["channel"], "text": c["text"], "acl": c["acl"],
                      "date": c["date"], "author": c["author"], "channel": c["channel"]})
    for t in _read(DATA / "tasks.json", []):
        t = _clean(t)
        items.append({"id": t["id"], "kind": "task", "title": t["title"], "text": t["title"], "acl": t["acl"],
                      "date": t.get("due", ""), "author": t["owner"], **{k: t[k] for k in t if k not in ("id", "title", "acl")}})
    for fname, kind in (("calendar.json", "calendar"), ("canva.json", "canva"), ("instagram.json", "instagram")):
        for x in _read(DATA / fname, []):
            x = _clean(x)
            items.append({"id": x["id"], "kind": kind, "title": x["title"], "text": x["text"], "acl": x["acl"],
                          "date": x["date"], "author": x.get("author", "")})
    for x in _read(STATE / "stripe_syncs.json", []):
        items.append({"id": x["id"], "kind": "stripe", "title": x["title"], "text": x["text"], "acl": x["acl"],
                      "date": x["date"], "author": "stripe"})
    for n in notes():
        items.append({"id": n["id"], "kind": "note", "title": n["title"], "text": n["text"], "acl": n["acl"],
                      "date": n["date"], "author": n["author"]})
    items.extend(_docs())
    return items


def source_by_id() -> dict:
    return {s["id"]: s for s in sources()}


def tasks() -> list:
    return [_clean(t) for t in _read(DATA / "tasks.json", [])]


# ---------- runtime state ----------
def memory() -> list:
    mem = _read(STATE / "memory.json", None)
    if mem is None:
        mem = [_clean(m) for m in _read(DATA / "memory_seed.json", [])]
        _write(STATE / "memory.json", mem)
    return mem


def save_memory(items: list) -> None:
    _write(STATE / "memory.json", items)


def actions() -> list:
    return _read(STATE / "actions.json", [])


def save_actions(items: list) -> None:
    _write(STATE / "actions.json", items)


def outbox() -> list:
    return _read(STATE / "outbox.json", [])


def save_outbox(items: list) -> None:
    _write(STATE / "outbox.json", items)


def briefs() -> dict:
    return _read(STATE / "briefs.json", {})


def save_briefs(value: dict) -> None:
    _write(STATE / "briefs.json", value)


def incoming() -> list:
    """Emails that 'arrived' during the demo (Simulate new email)."""
    return _read(STATE / "incoming.json", [])


def save_incoming(items: list) -> None:
    _write(STATE / "incoming.json", items)


SNAPSHOT = BUILD / "demo_snapshot"


def reset_demo() -> None:
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir(parents=True, exist_ok=True)


def has_snapshot() -> bool:
    return (SNAPSHOT / "briefs.json").exists()


def restore_snapshot() -> None:
    """Instant reset for the demo: the 08:00 briefs and proposals Jarvis made earlier with Gemini (nobody asked)."""
    reset_demo()
    for name in ("briefs.json", "actions.json", "memory.json", "audit.jsonl"):
        if (SNAPSHOT / name).exists():
            shutil.copy(SNAPSHOT / name, STATE / name)


def save_snapshot() -> None:
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    for name in ("briefs.json", "actions.json", "memory.json", "audit.jsonl"):
        if (STATE / name).exists():
            shutil.copy(STATE / name, SNAPSHOT / name)


def calls() -> list:
    return _read(STATE / "calls.json", [])


def save_calls(items: list) -> None:
    _write(STATE / "calls.json", items)


def notes() -> list:
    """Knowledge people typed in themselves (not from Gmail/Notion): each note is a citable source."""
    return _read(STATE / "notes.json", [])


def save_notes(items: list) -> None:
    _write(STATE / "notes.json", items)


def audiences() -> dict:
    """Groups Jarvis may draft announcements to (e.g. a cohort of students). Fake data in the demo."""
    return {a["id"]: a for a in company().get("audiences", [])}


def label(recipient: str) -> str:
    """Human name for any recipient id: a person, a tutor, a student group, or an email address."""
    if recipient in team():
        return team()[recipient]["name"]
    if recipient in audiences():
        a = audiences()[recipient]
        return f"{a['name']} ({a['size']})"
    src = source_by_id().get(recipient)
    if src and src["kind"] == "notion":
        return src["title"]
    return recipient
