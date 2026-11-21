"""Jarvis for PoliPrep: Arif's build of Challenge A (Company Brain).
Run from builds/arif:  .venv\\Scripts\\python -m streamlit run app.py
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from brain import access, answer, audit, brief, call, llm, memory, phone, propose, store, stripe_sync, voice, watch  # noqa: E402
from ui.orb import orb  # noqa: E402

st.set_page_config(page_title=f"Jarvis · {store.company_name()}", page_icon=":material/support_agent:", layout="wide")

# HUD: dark field, 1px cyan hairlines, corner brackets. Chakra Petch for display, Plex Sans for text, Plex Mono for ids and numbers.
st.html("<style>" + (Path(__file__).resolve().parent / "ui" / "hud.css").read_text(encoding="utf-8") + "</style>")

PEOPLE = store.people()
PAGES = [":material/wb_sunny: Today", ":material/inventory_2: Memory", ":material/task_alt: Approvals",
         ":material/mail: Morning email", ":material/receipt_long: Audit log"]
WHEN = {"high": "Today", "medium": "This week", "low": "For info"}
ss = st.session_state
ss.setdefault("user", "arif")
ss.setdefault("page", PAGES[0])
ss.setdefault("prefill", "")
ss.setdefault("chat", {})
ss.setdefault("channel", "Jarvis")

if not store.briefs():
    if store.has_snapshot():
        store.restore_snapshot()
    else:
        with st.spinner("Jarvis is preparing everyone's 08:00 brief…"):
            brief.sweep()

MARK = ("<svg width='28' height='28' viewBox='0 0 200 200' fill='none' stroke='#5CE1E6' stroke-width='9' aria-hidden='true'>"
        "<polygon points='145,74 145,126 100,152 55,126 55,74 100,48'/><polygon points='100,72 124,114 76,114' stroke-width='7'/>"
        "<circle cx='100' cy='100' r='92' stroke-width='5' stroke-opacity='.45'/></svg>")


# ---------- helpers ----------
def name(uid: str) -> str:
    p = store.team().get(uid)
    return p["name"] if p else uid


def first(uid: str) -> str:
    return name(uid).split()[0]


def goto(page: str, user: str | None = None, prefill: str = "") -> None:
    ss.page = page
    if user:
        ss.user = user
    ss.prefill = prefill
    ss.channel = "Jarvis"


def do_reset() -> None:
    """Instant: restores the 08:00 briefs Jarvis made earlier. 'Run 08:00 sweep' regenerates them live."""
    ss.chat = {}
    ss.prefill = ""
    ss.pop("brief_voice", None)
    if store.has_snapshot():
        store.restore_snapshot()
    else:
        store.reset_demo()
        brief.sweep()


def do_sweep() -> None:
    brief.sweep()


def do_new_email() -> None:
    ss.last_watch = watch.new_email_arrives()


def do_stripe_sync() -> None:
    try:
        out = stripe_sync.sync(ss.user)
        tot = out["summary"]["total"]
        ss.stripe_result = {"user": ss.user, "origin": out["origin"], "net": f"EUR {tot['net'] / 100:,.0f}",
                            "payments": tot["payments"], "conflicts": [c["id"] for c in out["conflicts"]]}
    except Exception as e:  # never crash the demo
        ss.stripe_result = {"user": ss.user, "error": str(e)[:200]}


def do_urgent_email() -> None:
    ss.last_watch = watch.new_email_arrives(store.demo_events().get("urgent_email") or watch.URGENT_EMAIL)
    if ss.last_watch.get("call"):
        ss.user = next((c["to"] for c in store.calls() if c["id"] == ss.last_watch["call"]), ss.user)
        ss.page = PAGES[0]


def do_play_brief(user: str) -> None:
    """Show the speaking orb for this user's brief; a fresh nonce lets it speak once."""
    ss.brief_voice = {"user": user, "n": ss.get("brief_voice", {}).get("n", 0) + 1}


def do_hide_brief() -> None:
    ss.pop("brief_voice", None)


def norm(q: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", q.lower()).strip()


def check_status() -> dict:
    rows = audit.read()
    asks = [r for r in rows if r["event"] == "ask"]
    approved = {r["mem_id"] for r in rows if r["event"] == "memory_approved"}
    return {
        1: any(r["event"] in ("brief_posted", "alert_posted") and r.get("unprompted") for r in rows),
        2: bool(approved) and any(r["event"] == "memory_rejected" for r in rows)
           and any(a["known"] and set(a.get("cited", [])) & approved for a in asks),
        3: any(a["known"] and not b["known"] and a["user"] != b["user"] and norm(a["question"]) == norm(b["question"])
               for a in asks for b in asks),
        4: any(a["known"] and a.get("cited") for a in asks),
        5: any(not a["known"] for a in asks),
        6: any(r["event"] == "action_proposed" for r in rows) and any(r["event"] == "action_approved" for r in rows),
        7: any(r["event"] == "viewed" and r.get("page") in ("brain", "email") for r in rows),
    }


def mark_viewed(page: str) -> None:
    key = f"viewed-{page}"
    if not ss.get(key):
        ss[key] = True
        audit.log("viewed", ss.user, page=page)


def clean(text: str) -> str:
    return text.replace("⚠️", "").strip()


def md(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def section(title: str, n: int | None = None, first_in_panel: bool = False, note: str = "") -> None:
    count = f"<span class='n'>{n}</span>" if n is not None else ""
    md(f"<div class='section{' first' if first_in_panel else ''}'>{html.escape(title)}{count}</div>"
       + (f"<div class='who'>{note}</div>" if note else ""))


def rise(scope: str, i: int):
    """A row container that rises in: 8px + fade, 40 ms stagger, capped so the whole list lands under 500 ms."""
    return st.container(key=f"rise{min(i, 4)}-{scope}-{i}")


def sources_block(ids: list, user: str) -> None:
    """Every claim shows where it came from: memory item → original email, chat, task or doc."""
    if not ids:
        return
    mem = {m["id"]: m for m in access.visible(store.memory(), user)}
    src = {s["id"]: s for s in access.visible(store.sources(), user)}
    with st.expander(f"Sources · `{', '.join(ids)}`"):
        for cid in ids:
            if cid in mem:
                m = mem[cid]
                md(f"<span class='ids cy'>{cid}</span> <span class='ids'>· memory · {m['status']}</span>")
                st.write(m["fact"])
                for sid in m["sources"]:
                    if sid in src:
                        s = src[sid]
                        md(f"<span class='ids cy'>{sid}</span> <span class='ids'>· {s['kind']} · {html.escape(str(s.get('author', '')))} · {s['date'][:10]}</span>")
                        st.write(f"**{s['title']}**: {s['text']}")
            elif cid in src:
                s = src[cid]
                md(f"<span class='ids cy'>{cid}</span> <span class='ids'>· {s['kind']} · {html.escape(str(s.get('author', '')))} · {s['date'][:10]}</span>")
                st.write(f"**{s['title']}**: {s['text']}")


def brief_row(it: dict, user: str, scope: str, i: int) -> None:
    with rise(scope, i):
        if it.get("security") or it["text"].startswith("⚠️"):
            md(f"<div class='row blocked'><div class='when high'>Blocked</div><div class='txt'>{html.escape(clean(it['text']))}</div></div>")
        else:
            u = it.get("urgency", "medium")
            md(f"<div class='row'><div class='when {u}'>{WHEN.get(u, 'This week')}</div><div class='txt'>{html.escape(clean(it['text']))}</div></div>")
        sources_block(it.get("cited", []), user)


def kind_label(a: dict) -> str:
    """Who an action goes to, in words: 'message colleague to Anna', 'announcement to students: CEnT-S Cohort 1 students (14)'."""
    if a["type"] == "announcement":
        return f"announcement to students: {store.label(a['to'])}"
    if a["type"] == "zoom_meeting":
        m = a.get("meeting", {})
        return "Zoom meeting with " + ", ".join(store.label(i) for i in m.get("with", [a["to"]]))
    return f"{a['type'].replace('_', ' ')} to {store.label(a['to'])}"


def do_harvest(cid: str, user: str) -> None:
    """Turn what was asked for on the real phone call into drafts. Only on click: it makes network calls."""
    before = next((x for x in store.calls() if x["id"] == cid), {}).get("harvested")
    try:
        new = call.harvest(cid, user)
    except Exception as e:  # never crash the demo
        res = ("error", f"Couldn't collect the drafts: {e}")
    else:
        after = next((x for x in store.calls() if x["id"] == cid), {}).get("harvested")
        res = ("added", len(new)) if new else ("already", 0) if before else ("none", 0) if after else ("waiting", 0)
    ss.setdefault("harvest", {})[cid] = res


def harvest_block(c: dict, user: str) -> None:
    res = ss.get("harvest", {}).get(c["id"])
    hc1, hc2, _ = st.columns([1.6, 1.3, 2.1])
    hc1.button("Collect drafts from the call", key=f"harvest-{c['id']}", icon=":material/move_to_inbox:",
               on_click=do_harvest, args=(c["id"], user), width="stretch")
    if not res:
        md("<div class='call-note'>After you hang up, Jarvis turns what you asked for on the phone into drafts that wait for approval.</div>")
        return
    kind, n = res
    if kind == "added":
        hc2.button("Open Approvals", key=f"harvest-go-{c['id']}", icon=":material/task_alt:", type="primary",
                   on_click=goto, args=(PAGES[2],), width="stretch")
        st.success(f"Added {n} draft{'' if n == 1 else 's'} to Approvals. Nothing is sent until you approve.", icon=":material/check_circle:")
    elif kind == "waiting":
        st.info("Call still in progress, try again when you hang up.", icon=":material/hourglass_top:")
    elif kind == "already":
        st.info("Already collected.", icon=":material/info:")
    elif kind == "none":
        st.info("Collected: nothing on the call needed a draft.", icon=":material/info:")
    else:
        st.error(n, icon=":material/error:")


# ---------- memory page: conflicts, edits, history ----------
def stamp(ts: str | None) -> str:
    try:
        return datetime.fromisoformat(str(ts)).strftime("%d %b %H:%M")
    except ValueError:
        return ""


def flash(where: str, kind: str, msg: str) -> None:
    ss.mem_flash = {"where": where, "kind": kind, "msg": msg}


def show_flash(where: str, f: dict | None) -> None:
    if f and f["where"] == where:
        if f["kind"] == "success":
            st.success(f["msg"], icon=":material/check_circle:")
        else:
            st.error(f["msg"], icon=":material/error:")


def toggle_edit(mid: str, status: str) -> None:
    target = {"id": mid, "status": status}
    ss.editing = None if ss.get("editing") == target else target


def is_editing(m: dict) -> bool:
    return ss.get("editing") == {"id": m["id"], "status": m["status"]}


def do_replace(pid: str, user: str, old_ids: list) -> None:
    """Resolve a conflict: approve the new fact and retire the approved one(s) it contradicts."""
    try:
        memory.approve(pid, user, supersede=old_ids)
        flash("pending", "success", f"{pid} is approved. {', '.join(old_ids)} is no longer used and stays in History.")
    except (PermissionError, ValueError) as e:
        flash("pending", "error", str(e))
    except KeyError:
        flash("pending", "error", "That item no longer exists.")
    ss.editing = None


def conflict_block(m: dict, found: list) -> None:
    """New vs approved now, side by side, in amber. Jarvis keeps answering from the approved fact until a person chooses."""
    now = "".join(f"<div class='cf-side now'><div class='cf-k'>Approved now · <span class='ids cy'>{c['id']}</span></div>"
                  f"<div>{html.escape(c['fact'])}</div><div class='cf-why'>{html.escape(c['why'] or 'Different values')}</div></div>"
                  for c in found)
    md(f"<div class='row conflict'><div class='when medium'>Conflict</div><div class='txt'>"
       f"<div class='cf-grid'><div class='cf-side new'><div class='cf-k'>New · <span class='ids cy'>{m['id']}</span></div>"
       f"<div>{html.escape(m['fact'])}</div></div><div class='cf-stack'>{now}</div></div>"
       "<div class='cf-note'>Both can't be true. Jarvis keeps using the approved fact until you choose.</div></div></div>")


def edit_form(m: dict, user: str, groups: dict) -> None:
    """Pending: edited in place, still needs Approve. Approved: saved as a new version, the old one goes to History."""
    approved = m["status"] == "approved"
    mid = m["id"]
    with st.container(key=f"editbox-{mid}"):
        with st.form(f"edit-{mid}", border=False):
            text = st.text_area("Edit the fact", value=m["fact"], key=f"edit-text-{mid}", max_chars=500, height=96)
            options = list(dict.fromkeys(memory.shareable_groups(user) + list(m["acl"])))
            ea, eb, ec = st.columns([3, 1.7, 1], vertical_alignment="bottom")
            acl = ea.multiselect("Who can see it", options, default=list(m["acl"]), key=f"edit-acl-{mid}",
                                 format_func=lambda g: f"{g} · {groups.get(g, g)}")
            save = eb.form_submit_button("Save as new version" if approved else "Save edit", key=f"edit-save-{mid}",
                                         icon=":material/save:", type="primary", width="stretch")
            cancel = ec.form_submit_button("Cancel", key=f"edit-cancel-{mid}", width="stretch")
        if cancel:
            ss.editing = None
            st.rerun()
        if save:
            if not acl:
                st.error("Pick at least one group that can see it.", icon=":material/error:")
                return
            try:
                new = memory.edit(mid, user, text, None if set(acl) == set(m["acl"]) else acl)
            except (ValueError, PermissionError) as e:
                st.error(str(e), icon=":material/error:")
                return
            except KeyError:
                st.error("That item no longer exists.", icon=":material/error:")
                return
            ss.editing = None
            if approved:
                flash("approved", "success", f"Saved as {new['id']}; {mid} is kept in history.")
            else:
                flash(f"item:{mid}", "success", f"Edit saved. {mid} still needs your approval before Jarvis uses it.")
            st.rerun()


def history_row(m: dict, by_id: dict) -> tuple[str, str]:
    """(sort key, markup) for one superseded or rejected item."""
    who, when = m.get("reviewed_by"), m.get("reviewed_at")
    bits = [m["id"]]
    if m["status"] == "superseded":
        label = "Replaced"
        new = by_id.get(m.get("superseded_by", ""))
        if new and new.get("edited_from") == m["id"]:   # replaced by an edit: the editor made the change
            who, when = new.get("edited_by") or new.get("reviewed_by"), new.get("reviewed_at")
        if m.get("superseded_by"):
            bits.append(f"replaced by <span class='cy'>{m['superseded_by']}</span>")
    else:
        label = "Rejected"
    if m.get("edited_from"):
        bits.append(f"edited from {m['edited_from']}")
    if who:
        bits.append(f"by {html.escape(name(who))}" + (f" · {stamp(when)}" if stamp(when) else ""))
    return str(when or ""), (f"<div class='row past'><div class='when past'>{label}</div><div class='txt'><s>{html.escape(m['fact'])}</s>"
                             f"<span class='ids'>{' · '.join(bits)}</span></div></div>")


# ---------- sidebar ----------
with st.sidebar:
    md(f"<div class='wordmark'>{MARK}<b>JARVIS</b></div><div class='wordmark-sub'>for <span class='co'>{html.escape(store.company_name())}</span>"
       " · speaks first, asks before it acts</div>")
    st.selectbox("Signed in as", list(PEOPLE), key="user", format_func=lambda u: f"{PEOPLE[u]['name']} · {PEOPLE[u]['role']}")
    st.caption("Access: " + ", ".join(g for g in access.groups(ss.user) if g != "all") + ". Set here, never by what you type.")
    st.radio("Go to", PAGES, key="page", label_visibility="collapsed")

    md("<div class='side-h'>Demo controls</div>")
    st.button("Run the 08:00 sweep", icon=":material/schedule:", on_click=do_sweep, width="stretch",
              help="Jarvis writes everyone's brief and proposes actions, without anyone asking (live Gemini)")
    st.button("Reset the demo", icon=":material/restart_alt:", on_click=do_reset, width="stretch")
    st.button("New email arrives", icon=":material/mark_email_unread:", on_click=do_new_email, width="stretch")
    st.button("An URGENT email arrives", icon=":material/notification_important:", on_click=do_urgent_email, width="stretch",
              help="Jarvis decides it's urgent, phones the CEO with a spoken briefing, and prepares a fix that waits for approval")
    if ss.get("last_watch", {}).get("status") == "already received":
        st.warning("Jarvis already handled this email: it calls only once per email. Press **Reset the demo** to replay it.",
                   icon=":material/info:")
    if "exec" in access.groups(ss.user) or PEOPLE[ss.user]["role"] == "CFO":
        st.button("Sync Stripe → Notion", icon=":material/payments:", key="stripe-sync", on_click=do_stripe_sync, width="stretch",
                  help="Reads Stripe payments, proposes the revenue fact (flagged if Notion disagrees) and a Notion update. Both wait for approval.")
    sr = ss.get("stripe_result")
    if sr and sr.get("user") == ss.user:
        if sr.get("error"):
            st.error(sr["error"], icon=":material/error:")
        else:
            st.success(f"{sr['origin']}: net {sr['net']} from {sr['payments']} payments. "
                       + (f"Conflicts with {', '.join(sr['conflicts'])}: resolve it in Memory. " if sr["conflicts"] else "")
                       + "The Notion update waits in Approvals.", icon=":material/check_circle:")
            st.button("Review in Memory", key="stripe-go-memory", on_click=goto, args=(PAGES[1],), width="stretch")

    status = check_status()
    md(f"<div class='side-h'>Jury checklist <span class='n'>{sum(status.values())}/7</span></div>")
    checks = [
        (1, "It speaks first", PAGES[0], "arif", ""),
        (2, "People curate the memory", PAGES[1], "arif", "When is the TOLC-I live this week?"),
        (3, "It knows who's asking", PAGES[0], "hamid", "What is our Cohort 1 revenue so far?"),
        (4, "It cites", PAGES[0], "hamid", "What is our Cohort 1 revenue so far?"),
        (5, "It admits gaps", PAGES[0], "sara", "What is the 2027 ARCHED exam date?"),
        (6, "It only proposes", PAGES[2], "hamid", ""),
        (7, "It fits the team's day", PAGES[3], "arif", ""),
    ]
    for n, label, page, user, q in checks:
        st.button(f"{n}. {label}", key=f"chk{n}", on_click=goto, args=(page, user, q), width="stretch",
                  icon=":material/check_circle:" if status[n] else ":material/radio_button_unchecked:")
    done = ", ".join(f".st-key-chk{n} [data-testid='stIconMaterial']" for n in status if status[n])
    st.html("<style>[class*='st-key-chk'] [data-testid='stIconMaterial']{color:var(--text-3)}"
            + (f"{done}{{color:var(--green)}}" if done else "") + "</style>")
    md("<div class='chk'>Check 3: ask the revenue as Hamid (CFO), then as Sara (CTO). "
       "Check 2: approve <span class='ids'>mem-p01</span>, reject <span class='ids'>mem-p02</span>, then ask.</div>")

user = ss.user
me = PEOPLE[user]

# ---------- header ----------
h1, h2 = st.columns([3, 1])
with h2:
    if llm.mode() == "gemini":
        md(f"<div class='status'><span class='led'></span>Gemini <span class='mono'>{llm.MODEL}</span> · Vertex AI</div>")
    else:
        md("<div class='status'><span class='led off'></span>Offline fallback (no Gemini credentials)</div>")

# ---------- incoming call from Jarvis (mock phone, real ElevenLabs voice, optional real phone call) ----------
for c in call.calls_for(user):
    real = c.get("real_call") or {}
    can_harvest = bool(real.get("conversation_id"))   # only a REAL phone call has a transcript to collect drafts from
    ended = c["status"] == "ended"
    if ended and not (can_harvest and (not c.get("harvested") or c["id"] in ss.get("harvest", {}))):
        continue
    ringing = c["status"] == "ringing"
    fix = next((a for a in store.actions() if a["id"] == c.get("action")), None)
    fix_line = (f" · fix ready: {kind_label(fix)}, waiting for your approval") if fix and fix["status"] == "awaiting_approval" else ""
    title = "Jarvis is calling you" if ringing else ("Your call with Jarvis ended" if ended else "On the call with Jarvis")
    with st.container(key=f"callcard-{c['id']}"):
        pulse = "<span class='pulse'></span><span class='pulse p2'></span>" if ringing else ""
        md(f"<div class='call-head'><div class='ringer{'' if ringing else (' ended' if ended else ' live')}'>{pulse}"
           "<svg width='22' height='22' viewBox='0 0 24 24' fill='currentColor' aria-hidden='true'><path d='M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z'/></svg></div>"
           f"<div><div class='call-t'>{title}</div>"
           f"<div class='call-meta'>{html.escape(c['why'])} · source <span class='ids'>{c['source']}</span>{html.escape(fix_line)}</div></div></div>")

        if not ended and real.get("status") == "dialing":
            st.success(f"Jarvis is calling your phone now ({phone.callee_masked()}). Answer it to talk to Jarvis; approvals stay in this app.",
                       icon=":material/phone_in_talk:")
        elif not ended and real.get("status") == "failed":
            st.error(f"The phone call didn't go through: {real.get('error')}", icon=":material/phone_disabled:")

        if ended:
            pass
        elif ringing:
            a1, a2, a3, _ = st.columns([1, 1, 1.7, 1.3])
            a1.button("Answer here", key=f"ans-{c['id']}", icon=":material/call:", type="primary", on_click=call.answer, args=(c["id"], user), width="stretch")
            a2.button("Decline", key=f"dec-{c['id']}", icon=":material/call_end:", on_click=call.hang_up, args=(c["id"], user), width="stretch")
            if phone.configured() and real.get("status") != "dialing":
                label = "Try the phone again" if real.get("status") == "failed" else f"Ring my real phone ({phone.callee_masked()})"
                a3.button(label, key=f"ring-{c['id']}", icon=":material/phone_in_talk:",
                          on_click=call.dial_real_phone, args=(c,), width="stretch")
            if c.get("action"):
                st.button("Review the fix Jarvis prepared", key=f"rev-{c['id']}", icon=":material/task_alt:",
                          on_click=goto, args=(PAGES[2],))
            md("<div class='call-note'>On-screen phone for the demo. The real call goes out through ElevenLabs Agents and Twilio.</div>")
        else:
            oc, tc = st.columns([1.1, 2], gap="large", vertical_alignment="center")
            with oc:
                spoken = None
                if voice.available():
                    try:
                        spoken = voice.speak(f"call-{c['id']}", c["script"])
                    except Exception as e:  # never crash the demo
                        st.warning(f"Voice unavailable: {e}")
                if spoken:
                    orb(300, audio=spoken, nonce=f"call-{c['id']}", autoplay=True)
                else:
                    orb(260)
            with tc:
                md(f"<div class='script-label'>Jarvis says</div><div class='script'>“{html.escape(c['script'])}”</div>")
                b1, b2 = st.columns([1.5, 1])
                if c.get("action"):
                    b1.button("Review the fix Jarvis prepared", key=f"rev-{c['id']}", icon=":material/task_alt:", type="primary",
                              on_click=goto, args=(PAGES[2],), width="stretch")
                b2.button("Hang up", key=f"hang-{c['id']}", icon=":material/call_end:", on_click=call.hang_up, args=(c["id"], user), width="stretch")
        if can_harvest:
            harvest_block(c, user)

# ---------- pages ----------
if ss.page == PAGES[0]:
    mark_viewed("brain")
    b = store.briefs().get(user, {"items": []})
    items = b.get("alerts", []) + b["items"]
    pending = [a for a in propose.for_user(user) if a["status"] == "awaiting_approval"]
    with h1:
        o, g = st.columns([1, 4.4], vertical_alignment="center")
        with o:
            orb(136)
        with g:
            md(f"<div class='greet'>Good morning, {html.escape(first(user))}.</div>"
               f"<div class='sub'>Monday 23 November · <span class='num'>{len(items)}</span> things need you"
               + (f" · <span class='num wait'>{len(pending)}</span> waiting for your approval" if pending else "") + "</div>")

    left, right = st.columns([1, 3.2], gap="large")
    with left:
        channels = sorted({s["channel"] for s in access.visible(store.sources(), user) if s["kind"] == "chat"})
        st.radio("Workspace", ["Jarvis"] + channels, key="channel",
                 format_func=lambda c: "Jarvis (direct)" if c == "Jarvis" else c)
    with right:
        if ss.channel != "Jarvis":
            with st.container(key="panel-channel"):
                section(ss.channel, first_in_panel=True)
                msgs = sorted((s for s in access.visible(store.sources(), user) if s.get("channel") == ss.channel), key=lambda s: s["date"])
                for i, s in enumerate(msgs):
                    with rise("ch", i):
                        md(f"<div class='msgline'><div class='who'><b>{html.escape(name(s['author']))}</b> · "
                           f"<span class='ids'>{s['date'][5:16].replace('T', ' ')}</span></div>"
                           f"<div class='txt'>{html.escape(s['text'])}</div></div>")
        else:
            with st.container(key="panel-brief"):
                if b.get("alerts"):
                    section("New since 08:00", len(b["alerts"]), first_in_panel=True)
                    for i, it in enumerate(b["alerts"]):
                        brief_row(it, user, "al", i)
                section("Your 08:00 brief", first_in_panel=not b.get("alerts"),
                        note=f"Posted by Jarvis {html.escape(str(b.get('posted_at', '')))}. Nobody asked for it.")
                for i, it in enumerate(b["items"]):
                    brief_row(it, user, "br", i)
                bc1, bc2, _ = st.columns([1.3, 1.9, 1.6])
                if voice.available() and b["items"]:
                    bc1.button("Play my brief", key="brief-play", icon=":material/volume_up:", on_click=do_play_brief, args=(user,), width="stretch")
                if pending:
                    bc2.button(f"Review {len(pending)} waiting for approval", icon=":material/task_alt:", on_click=goto, args=(PAGES[2],), width="stretch")
                bv = ss.get("brief_voice")
                if bv and bv.get("user") == user and voice.available() and b["items"]:
                    text = f"Good morning {first(user)}. " + " ".join(clean(i["text"]) for i in b["items"])
                    try:
                        audio = voice.speak(user, text)
                    except Exception as e:  # never crash the demo
                        audio = None
                        st.warning(f"Voice unavailable: {e}")
                    if audio:
                        vo, vt = st.columns([1, 1.6], vertical_alignment="center")
                        with vo:
                            orb(240, audio=audio, nonce=f"brief-{user}-{bv['n']}", autoplay=True)
                        with vt:
                            md("<div class='script-label'>Your brief, read aloud</div>"
                               f"<div class='who'>{len(b['items'])} items in Jarvis's voice. Press Pause any time.</div>")
                            st.button("Close the player", key="brief-hide", icon=":material/close:", on_click=do_hide_brief)

            with st.container(key="panel-ask"):
                section("Ask Jarvis", first_in_panel=True,
                        note="Answers come only from team memory you may see, with sources. Otherwise: “I don't know”.")
                for i, qa in enumerate(ss.chat.get(user, [])):
                    with rise("qa", i):
                        md(f"<div class='q'>{html.escape(qa['question'])}</div>"
                           f"<div class='a{'' if qa['known'] else ' unknown'}'>{html.escape(qa['answer'])}</div>")
                        sources_block([c["mem_id"] for c in qa["citations"]], user)
                with st.form("ask", clear_on_submit=True, border=False):
                    fq, fb = st.columns([5, 1])
                    q = fq.text_input("Ask Jarvis", value=ss.prefill, placeholder="When is the TOLC-I live this week?", label_visibility="collapsed")
                    if fb.form_submit_button("Ask", type="primary", width="stretch") and q.strip():
                        ss.chat.setdefault(user, []).append(answer.ask(user, q))
                        ss.prefill = ""
                        st.rerun()

elif ss.page == PAGES[1]:
    with h1:
        md("<div class='greet'>Team memory</div><div class='sub'>Jarvis answers only from approved items. Each item keeps the access list of its source.</div>")
    groups = store.company().get("groups", {})
    with st.container(key="panel-note"):
        section("Add what you know", first_in_panel=True,
                note="Knowledge that isn't in Gmail or Notion. It's saved as approved by you and cited as your note.")
        with st.form("add-note", clear_on_submit=True, border=False):
            note_text = st.text_area("What should Jarvis know?", key="note-text", max_chars=500, height=96,
                                     placeholder="The accountant wants all Cohort 1 tutor receipts by 15 December.")
            na, nb = st.columns([3, 1.2], vertical_alignment="bottom")
            note_acl = na.multiselect("Who can see it", memory.shareable_groups(user), default=["all"], key="note-acl",
                                      format_func=lambda g: f"{g} · {groups.get(g, g)}")
            saved = nb.form_submit_button("Save to memory", icon=":material/add_task:", type="primary", width="stretch")
        if saved:
            try:
                item = memory.add_manual(user, note_text, note_acl)
                if item["status"] == "pending":
                    ids = [c["id"] for c in memory.conflicts(item["id"], user)]
                    st.warning(f"Your note contradicts {', '.join(ids) if ids else 'approved memory'}, so it went to review "
                               f"instead of being saved directly. Resolve {item['id']} below.", icon=":material/warning:")
                else:
                    st.success(f"Saved as {item['id']}, approved by you and cited as {', '.join(item['sources'])}.", icon=":material/check_circle:")
            except (ValueError, PermissionError) as e:
                st.error(str(e), icon=":material/error:")
    fl = ss.pop("mem_flash", None)
    pend = memory.pending_for(user)
    with st.container(key="panel-pending"):
        section("Waiting for your review", len(pend), first_in_panel=True)
        show_flash("pending", fl)
        if not pend:
            md("<div class='empty'>Nothing to review that you can see. New facts appear here when an email arrives.</div>")
        for i, m in enumerate(pend):
            found = memory.conflicts(m["id"], user)
            with rise("mp", i):
                edited = f" · edited by {html.escape(first(m['edited_by']))}" if m.get("edited_by") else ""
                md(f"<div class='row'><div class='when medium'>Pending</div><div class='txt'>{html.escape(m['fact'])}"
                   f"<span class='ids'>{m['id']} · proposed by {m.get('proposed_by', 'extractor')}{edited} · visible to {', '.join(m['acl'])}</span></div></div>")
                sources_block(m["sources"], user)
                if found:
                    conflict_block(m, found)
                    old = [c["id"] for c in found]
                    c1, c2, c3, _ = st.columns([2.3, 1, 1, 2.2])
                    c1.button(f"Approve and replace {', '.join(old)}", key=f"sup-{m['id']}", icon=":material/swap_horiz:", type="primary",
                              on_click=do_replace, args=(m["id"], user, old), width="stretch")
                else:
                    c1, c2, c3, _ = st.columns([1, 1, 1, 3])
                    c1.button("Approve", key=f"ap-{m['id']}", icon=":material/check:", type="primary", on_click=memory.approve, args=(m["id"], user), width="stretch")
                c2.button("Reject", key=f"rj-{m['id']}", icon=":material/close:", on_click=memory.reject, args=(m["id"], user), width="stretch")
                c3.button("Close" if is_editing(m) else "Edit", key=f"edt-{m['id']}", icon=":material/close:" if is_editing(m) else ":material/edit:",
                          on_click=toggle_edit, args=(m["id"], m["status"]), width="stretch")
                if is_editing(m):
                    edit_form(m, user, groups)
                show_flash(f"item:{m['id']}", fl)
    mem = store.memory()
    vis = access.visible(mem, user)
    appr = [x for x in vis if x["status"] == "approved"]
    with st.container(key="panel-approved"):
        section("Approved", len(appr), first_in_panel=True)
        show_flash("approved", fl)
        for i, m in enumerate(appr):
            with rise("ma", i):
                t, e = st.columns([10, 1.5], vertical_alignment="center")
                origin = f" · edited from {m['edited_from']}" if m.get("edited_from") else ""
                t.markdown(f"<div class='msgline'><div class='txt'>{html.escape(m['fact'])}</div>"
                           f"<span class='ids'>{m['id']} · {', '.join(m['sources'])}{origin}</span></div>", unsafe_allow_html=True)
                e.button("Close" if is_editing(m) else "Edit", key=f"edt-{m['id']}", icon=":material/close:" if is_editing(m) else ":material/edit:",
                         type="tertiary", on_click=toggle_edit, args=(m["id"], m["status"]), width="stretch")
                if is_editing(m):
                    edit_form(m, user, groups)
    by_id = {m["id"]: m for m in mem}
    hist = sorted((history_row(m, by_id) for m in memory.history_for(user)), key=lambda r: r[0], reverse=True)
    with st.container(key="panel-history"):
        section("History · superseded and rejected", len(hist), first_in_panel=True,
                note="Kept for the record. Jarvis never uses these to answer.")
        if not hist:
            md("<div class='empty'>Nothing replaced or rejected yet.</div>")
        else:
            md("".join(r[1] for r in hist[:4]))
        if len(hist) > 4:
            with st.expander(f"Show {len(hist) - 4} older"):
                md("".join(r[1] for r in hist[4:]))

elif ss.page == PAGES[2]:
    acts = propose.for_user(user)
    waiting = [a for a in acts if a["status"] == "awaiting_approval"]
    with h1:
        md(f"<div class='greet'>Approvals</div><div class='sub'><span class='num{' wait' if waiting else ''}'>{len(waiting)}</span> waiting. "
           "Jarvis has no tool that sends: nothing leaves until you approve it.</div>")
    with st.container(key="panel-actions"):
        section("Proposed by Jarvis", len(acts), first_in_panel=True)
        if not acts:
            md("<div class='empty'>Nothing proposed for you.</div>")
        for i, a in enumerate(acts):
            label = {"awaiting_approval": ("Waiting", "medium"), "approved": ("Sent", "low"), "rejected": ("Rejected", "high")}[a["status"]]
            with rise("ac", i):
                md(f"<div class='row'><div class='when {label[1]}'>{label[0]}</div><div class='txt'><b>{html.escape(a['subject'])}</b>"
                   f"<div class='who'>{html.escape(kind_label(a))} · why: {html.escape(a['reason'])}</div>"
                   f"<div style='margin-top:.5rem; white-space:pre-line'>{html.escape(a['body'])}</div>"
                   + (f"<div class='who' style='margin-top:.4rem'>Join: <span class='ids'>{html.escape(str(a['meeting']['join_url']))}</span>"
                      + ("" if a["meeting"].get("real") else " (demo link)") + "</div>"
                      if a.get("meeting", {}).get("join_url") else "")
                   + "</div></div>")
                sources_block(a["cites"], user)
                if a["status"] == "awaiting_approval":
                    c1, c2, _ = st.columns([1.4, 1, 2.6])
                    c1.button("Approve and send", key=f"aa-{a['id']}", icon=":material/send:", type="primary",
                              on_click=propose.approve_action, args=(a["id"], user), width="stretch")
                    c2.button("Reject", key=f"ar-{a['id']}", icon=":material/close:", on_click=propose.reject_action, args=(a["id"], user), width="stretch")
    box = [o for o in store.outbox() if o["proposed_to"] == user]
    with st.container(key="panel-outbox"):
        section("Outbox", len(box), first_in_panel=True, note="Mock: nothing leaves this demo.")
        for i, o in enumerate(box):
            with rise("ob", i):
                md(f"<div class='msgline'><div class='txt'><b>{html.escape(o['subject'])}</b> to {html.escape(store.label(o['to']))}</div>"
                   f"<span class='ids'>approved by {html.escape(name(o['decided_by']))} at {o['decided_at'][11:16]}"
                   + (f" · {html.escape(o['sent'])}" if o.get("type") == "zoom_meeting" else "") + "</span></div>")

elif ss.page == PAGES[3]:
    mark_viewed("email")
    b = store.briefs().get(user, {"items": []})
    items = b.get("alerts", []) + b["items"]
    with h1:
        md("<div class='greet'>Morning email</div><div class='sub'>Where the team meets Jarvis at 08:00, before opening anything else.</div>")
    lis = "".join(f"<li>{html.escape(clean(i['text']))} <span class='ids'>[{', '.join(i.get('cited', []))}]</span></li>" for i in items)
    n_pending = sum(a["status"] == "awaiting_approval" for a in propose.for_user(user))
    md(f"""<div class="mail hud-panel"><div class="meta"><span>From Jarvis <span class="mono">&lt;jarvis@poliprep.example&gt;</span></span><span>To {html.escape(me['name'])}</span><span>Monday 23 November, <span class="mono">08:00</span></span></div>
<h3>Good morning {html.escape(first(user))}: {len(items)} things need you today</h3><ol>{lis}</ol>
<p><b>{n_pending} waiting for your approval.</b> Nothing is sent until you approve it in Jarvis.</p>
<p class="who">Every item cites its source. Jarvis only uses memory your team approved and that your role may see. Mock-up: no real email is sent.</p></div>""")

else:
    with h1:
        md("<div class='greet'>Audit log</div><div class='sub'>Everything Jarvis did: who asked, what it cited, what it proposed, who approved.</div>")
    # lists as text: some events log one id, others a list, and mixed column types break the table
    rows = [{k: ", ".join(map(str, v)) if isinstance(v, list) else v for k, v in r.items()} for r in reversed(audit.read())]
    st.dataframe(rows, width="stretch", height=460)
    u = llm.USAGE
    if u["calls"]:
        st.caption(f"This session: {u['calls']} Gemini calls, {u['input_tokens']} input + {u['output_tokens']} output tokens ≈ ${llm.cost_eur_estimate():.4f} at list price.")
