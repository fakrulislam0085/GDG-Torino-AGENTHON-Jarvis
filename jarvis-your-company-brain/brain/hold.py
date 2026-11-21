"""The cold open (ported): a Wednesday-night frost warning arrives after the team already planned the Thursday
repair, so the waiting customer reply is HELD and one internal request to move the repair up waits for the sales
owner. Code decides from the two dates; a person still decides everything else.

Presentation only beyond the one request: the case context adds no people, permissions, notifications or decisions.
Slack, Discord, text and Drive are simulated sources; the customer email and the engineering chat are real records.
"""
from __future__ import annotations

import re
from datetime import date

from . import access, audit, propose, store

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_DATE = re.compile(r"\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+(\d{4}))?", re.I)
NIGHT = re.compile(r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\s+(?:night|evening)\b", re.I)
WEEKDAY = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I)
CLOCK = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")

# The messages the cold open piles up. Presentation only.
CASE_CONTEXT = [
    {"who": "Davide Greco", "role": "Engineering", "source": "Slack · engineering chat",
     "text": "GW-07 rollout. Thursday 26 November, 07:00.", "simulated": True},
    {"who": "Stefano, Cantina Langhe Viva", "role": "Vineyard customer", "source": "Customer email",
     "text": "Frost is forecast Wednesday night, 25 November. Can you confirm coverage?", "cites": ["email-101"], "simulated": False},
    {"who": "Paolo Gallo", "role": "Sales", "source": "Unsent customer reply",
     "text": "Drafted an update using Thursday's plan. It is waiting for approval.", "simulated": False},
    {"who": "Sara Conti", "role": "Technical support", "source": "Slack",
     "text": "Forty are still offline.", "simulated": True},
    {"who": "Marco Rossi", "role": "Engineering", "source": "Discord",
     "text": "I'm checking the spare gateway.", "simulated": True},
    {"who": "Marta", "role": "Dispatch", "source": "Text message",
     "text": "No earlier slot confirmed.", "simulated": True},
    {"who": "Luca Bianchi", "role": "Operations", "source": "Drive",
     "text": "That's the old service plan.", "simulated": True},
    {"who": "Elena Russo", "role": "Leadership", "source": "Slack DM",
     "text": "What can we actually tell the customer?", "simulated": True},
    {"who": "Stefano, Cantina Langhe Viva", "role": "Vineyard customer", "source": "Text follow-up",
     "text": "Can someone confirm today?", "simulated": True},
]


def _dates(text: str, year: int) -> list[date]:
    out = []
    for d, mon, y in _DATE.findall(text or ""):
        try:
            out.append(date(int(y) if y else year, MONTHS[mon.lower()], int(d)))
        except ValueError:
            pass
    return out


def _when(src_text: str) -> str:
    wd, clock = WEEKDAY.search(src_text or ""), CLOCK.search(src_text or "")
    return ", ".join(x for x in [wd.group(1).capitalize() if wd else None, clock.group(0) if clock else None] if x)


def _waiting_reply(contact: str):
    """The waiting reply to this customer, whoever it was proposed to."""
    return next((a for a in store.actions()
                 if a["type"] == "reply_draft" and a["to"] == contact and a["status"] == "awaiting_approval"), None)


def _engineer(email: dict, approver: str) -> str | None:
    return next((u for u in email.get("cc", []) if u in store.team() and u != approver), None)


def apply(email: dict) -> dict | None:
    """After a normal email arrives: if the customer needs coverage before the scheduled repair, hold the waiting
    reply and raise one internal request to the engineer. Returns the hold record, or None."""
    spec = store.demo_events().get("frost_warning") or {}
    if not spec or email.get("id") != spec.get("id"):
        return None
    contact, year = email["from"], store.demo_now().year
    draft = _waiting_reply(contact)
    plan = store.source_by_id().get(spec.get("hold_plan_source", ""))
    if not draft or not plan:
        return None
    need, planned = sorted(set(_dates(email["body"], year))), sorted(set(_dates(plan["text"], year)))
    if len(need) != 1 or len(planned) != 1 or not need[0] < planned[0]:
        return None
    approver = draft["proposed_to"]
    night = NIGHT.search(email["body"])
    acts = store.actions()
    for a in acts:
        if a["id"] == draft["id"]:
            a["status"] = "held"
            a["hold_reason"] = (f"New evidence from {email['id']}: the customer needs coverage "
                                f"{need[0]:%a %d %b}, but the {plan['id']} rollout is {planned[0]:%a %d %b}. "
                                "Review it before anything is sent.")
            a["hold_sources"] = [email["id"], plan["id"]]
            a["evidence"] = [
                {"text": "Customer needs coverage " + (night.group(0)[:1].upper() + night.group(0)[1:].lower()
                                                       if night else f"by {need[0]:%a %d %b}"), "cites": [email["id"]]},
                {"text": "Engineering rollout scheduled " + (_when(plan["text"]) or f"{planned[0]:%a %d %b}"),
                 "cites": [plan["id"]]}]
    store.save_actions(acts)
    audit.log("draft_held", approver, action_id=draft["id"], sources=[email["id"], plan["id"]])
    engineer = _engineer(email, approver)
    if engineer:
        propose.add(approver, "message_colleague", engineer,
                    f"Langhe Viva: can the gateway be fixed before {(_when(plan['text']) or 'Thursday')}?",
                    f"Hi {store.team()[engineer]['name'].split()[0]}, Stefano at Langhe Viva expects -4 °C on "
                    f"{night.group(0).title() if night else 'the coming night'} and is blind without the 40 sensors on GW-07. "
                    f"The firmware 2.3 rollout is planned for {_when(plan['text']) or 'Thursday'}. Can we bring it forward, "
                    "or install the spare gateway first? I promised him an answer today. Paolo",
                    f"Jarvis escalated {email['id']}: move the repair up or use the spare gateway",
                    [email["id"], plan["id"]])
    return {"held": draft["id"], "internal": engineer}


def case_context(user_id: str) -> list[dict]:
    """The film's messages, shown only once the cold-open email actually arrived and only to someone who may see it."""
    spec = store.demo_events().get("frost_warning") or {}
    src = store.source_by_id().get(spec.get("id", ""))
    if not src or not any(e.get("id") == src["id"] for e in store.incoming()) or not access.can_see(src, user_id):
        return []
    return CASE_CONTEXT


def timeline(a: dict) -> str:
    """The film's two-source miniature: the customer email, the engineering chat, the verdict, the two outcomes."""
    import html as _h
    rows = "".join(
        f"<div class='tl-step'><b>{_h.escape(str(ev['text']))}</b> · {_h.escape(_label(ev['cites'][0]))} "
        f"<span class='ids'>{_h.escape(', '.join(ev['cites']))}</span></div>"
        + ("<div class='tl-arrow'>↓</div>" if i < len(a.get("evidence", [])) - 1 else "")
        for i, ev in enumerate(a.get("evidence", [])))
    return (f"<div class='timeline'>{rows}<div class='tl-arrow'>↓</div>"
            "<div class='tl-verdict'>Rollout is scheduled after coverage is needed</div><div class='tl-arrow'>↓</div>"
            "<div class='tl-outcome'>Customer reply held · Internal request to the engineer waiting on "
            + _h.escape(store.team().get(a.get("proposed_to", ""), {}).get("name", "").split()[0]) + "</div></div>")


def _label(sid: str) -> str:
    kind = store.source_by_id().get(sid, {}).get("kind")
    return {"chat": "Engineering chat", "email": "Customer email", "doc": "Drive document", "task": "Task"}.get(kind, kind or "source")
