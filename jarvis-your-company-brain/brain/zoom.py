"""Zoom: Jarvis proposes meetings; a meeting is created only after a person taps Approve.

Real Zoom: a Server-to-Server OAuth app (Zoom Marketplace) with scope to create meetings, and in jarvis-your-company-brain/.env:
ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET. Without them (or in offline/test mode) the join link is a labelled demo link.
"""
from __future__ import annotations

import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from . import audit, store

load_dotenv(store.BUILD / ".env", override=True)
TZ = "Europe/Rome"


def configured() -> bool:
    return all(os.getenv(k) for k in ("ZOOM_ACCOUNT_ID", "ZOOM_CLIENT_ID", "ZOOM_CLIENT_SECRET")) \
        and os.getenv("BRAIN_MODE", "").lower() != "offline"


def _token() -> str:
    r = requests.post("https://zoom.us/oauth/token",
                      params={"grant_type": "account_credentials", "account_id": os.environ["ZOOM_ACCOUNT_ID"]},
                      auth=(os.environ["ZOOM_CLIENT_ID"], os.environ["ZOOM_CLIENT_SECRET"]), timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]


def valid_meeting(m: dict) -> dict | None:
    """Clean a proposed meeting: topic, start (YYYY-MM-DDTHH:MM, Rome time), 10-60 minutes, invitees = team ids."""
    try:
        start = datetime.fromisoformat(str(m.get("start", ""))[:16])
    except ValueError:
        return None
    try:
        minutes = max(10, min(60, int(m.get("minutes") or 15)))
    except (TypeError, ValueError):
        minutes = 15
    team = store.team()
    invitees = [i for i in (m.get("with") or []) if i in team]
    topic = str(m.get("topic") or "").strip()[:120]
    if not topic or not invitees:
        return None
    return {"topic": topic, "start": start.strftime("%Y-%m-%dT%H:%M"), "minutes": minutes, "with": invitees, "timezone": TZ}


def create(meeting: dict) -> dict:
    """Called only from an approved action. Returns join_url and whether it is real or a demo link."""
    if not configured():
        link = f"https://zoom.us/j/demo-{abs(hash((meeting['topic'], meeting['start']))) % 10**10}"
        return {"join_url": link, "real": False, "note": "demo link: add Zoom keys to create real meetings"}
    r = requests.post("https://api.zoom.us/v2/users/me/meetings", timeout=20,
                      headers={"Authorization": f"Bearer {_token()}"},
                      json={"topic": meeting["topic"], "type": 2, "start_time": meeting["start"] + ":00",
                            "timezone": meeting.get("timezone", TZ), "duration": meeting["minutes"],
                            "agenda": "Proposed by Jarvis, approved by a person.",
                            "settings": {"waiting_room": True, "join_before_host": False}})
    if r.status_code >= 400:
        raise RuntimeError(f"Zoom refused: {r.status_code} {r.text[:200]}")
    out = r.json()
    return {"join_url": out.get("join_url"), "meeting_id": out.get("id"), "real": True}
