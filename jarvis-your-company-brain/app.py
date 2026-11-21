"""Jarvis, best-of-three build: Company Brain (Challenge A) on the Filare Labs demo data, light theme.
Everything company-specific (people, checklist, default user, placeholders, pages) comes from <JARVIS_DATA>/company.json
(default data_filare: Filare Labs).
Run from jarvis-your-company-brain:  ..\\arif\\.venv\\Scripts\\python -m streamlit run app.py --server.port 8504
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from brain import access, answer, audit, brief, call, llm, memory, phone, propose, store, stripe_sync, voice, watch  # noqa: E402
from ui import counts as tally  # noqa: E402
from ui.orb import orb  # noqa: E402
from ui.voice_chat import voice_chat  # noqa: E402

st.set_page_config(page_title=f"Jarvis · {store.short_name()}", page_icon=":material/support_agent:", layout="wide")

# Light HUD: near-white field, white panels, 1px teal hairlines, corner brackets. Chakra Petch display, Plex Sans text, Plex Mono ids.
st.html("<style>" + (Path(__file__).resolve().parent / "ui" / "hud.css").read_text(encoding="utf-8") + "</style>")

PEOPLE = store.people()
DEMO = store.demo()
PAGES = [":material/wb_sunny: Today", ":material/inventory_2: Memory", ":material/task_alt: Approvals",
         ":material/mail: Morning email", ":material/receipt_long: Audit log"]
PAGE_KEYS = {"today": PAGES[0], "memory": PAGES[1], "approvals": PAGES[2], "email": PAGES[3], "audit": PAGES[4]}
WHEN = {"high": "Today", "medium": "This week", "low": "For info"}
NOW = store.demo_now()
ss = st.session_state
default_user = DEMO.get("default_user") if DEMO.get("default_user") in PEOPLE else (store.ceo() or next(iter(PEOPLE)))
ss.setdefault("user", default_user)
if ss.user not in PEOPLE:
    ss.user = default_user
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

MARK = ("<svg width='28' height='28' viewBox='0 0 200 200' fill='none' stroke='#0E7C86' stroke-width='9' aria-hidden='true'>"
        "<polygon points='145,74 145,126 100,152 55,126 55,74 100,48'/><polygon points='100,72 124,114 76,114' stroke-width='7'/>"
        "<circle cx='100' cy='100' r='92' stroke-width='5' stroke-opacity='.45'/></svg>")


# ---------- helpers ----------
def name(uid: str) -> str:
    p = store.team().get(uid)
    return p["name"] if p else uid


def first(uid: str) -> str:
    return name(uid).split()[0]


def is_ceo(uid: str) -> bool:
    return "exec" in access.groups(uid)


def goto(page: str, user: str | None = None, prefill: str = "") -> None:
    ss.page = page
    if user:
        ss.user = user
    ss.prefill = prefill
    ss.channel = "Jarvis"


def do_reset() -> None:
    """CEO only. Instant: restores the 08:00 briefs Jarvis made earlier. 'Run 08:00 sweep' regenerates them live."""
    if not is_ceo(ss.user):
        return
    ss.chat = {}
    ss.prefill = ""
    for k in ("brief_voice", "voice_chat", "decide", "editing", "edit_action", "stripe_result", "paste_result", "last_watch", "harvest",
              "export_ready"):
        ss.pop(k, None)
    llm.reset_breaker()
    if store.has_snapshot():
        store.restore_snapshot()
    else:
        store.reset_demo()
        brief.sweep()


def do_sweep() -> None:
    brief.sweep("manual")


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


def do_talk(user: str) -> None:
    """Open (or reopen) the live voice chat: a fresh nonce fetches a fresh short-lived signed URL."""
    ss.voice_chat = {"user": user, "n": ss.get("voice_chat", {}).get("n", 0) + 1, "session": None}


def do_close_talk() -> None:
    ss.pop("voice_chat", None)


def do_ask(user: str, q: str) -> None:
    """One code path for the Ask button and the one-tap chips: ask as this person, keep the answer in their chat."""
    q = (q or "").strip()
    if q:
        ss.chat.setdefault(user, []).append(answer.ask(user, q))
    ss.prefill = ""


def do_chip(q: str) -> None:
    """A question chip: fills the question and asks it as whoever is signed in now (check 3: switch user, same chip)."""
    do_ask(ss.user, q)


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


def md(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x))


def section(title: str, n: int | None = None, first_in_panel: bool = False, note: str = "") -> None:
    count = f"<span class='n'>{n}</span>" if n is not None else ""
    md(f"<div class='section{' first' if first_in_panel else ''}'>{esc(title)}{count}</div>"
       + (f"<div class='who'>{note}</div>" if note else ""))


def rise(scope: str, i: int):
    """A row container that rises in: 8px + fade, 40 ms stagger, capped so the whole list lands under 500 ms."""
    return st.container(key=f"rise{min(i, 4)}-{scope}-{i}")


def stamp(ts: str | None) -> str:
    try:
        return datetime.fromisoformat(str(ts)).strftime("%d %b %H:%M")
    except ValueError:
        return ""


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
                        md(f"<span class='ids cy'>{sid}</span> <span class='ids'>· {s['kind']} · {esc(s.get('author', ''))} · {s['date'][:10]}</span>")
                        st.write(f"**{s['title']}**: {s['text']}")
            elif cid in src:
                s = src[cid]
                md(f"<span class='ids cy'>{cid}</span> <span class='ids'>· {s['kind']} · {esc(s.get('author', ''))} · {s['date'][:10]}</span>")
                st.write(f"**{s['title']}**: {s['text']}")


def how_block(qa: dict) -> None:
    """'How I got this' (graft from builds/daddy): the role filter, which facts were considered and cited, the number check, the mode.
    Ids only for facts this person may see; restricted content is never shown."""
    t = qa.get("trace")
    if not t:
        return
    with st.expander("How I got this", icon=":material/route:"):
        groups = ", ".join(t.get("groups") or []) or "everyone"
        lines = [f"<b>Role filter</b> (code, before any model call): {esc(t.get('asked_by', ''))} may see "
                 f"<span class='num'>{t.get('visible', 0)}</span> of <span class='num'>{t.get('total', 0)}</span> approved facts "
                 f"(groups: {esc(groups)}). Raw emails and unapproved notes are never used to answer."]
        considered = t.get("considered") or []
        lines.append("<b>Considered:</b> " + (f"<span class='ids cy'>{esc(', '.join(considered))}</span>" if considered else "none"))
        cited = t.get("cited") or []
        lines.append("<b>Cited:</b> " + (f"<span class='ids cy'>{esc(', '.join(cited))}</span>" if cited else "none"))
        if t.get("number_check") == "replaced":
            lines.append("<b>Number check:</b> the model's text had a number the cited facts don't contain, so I show the approved facts word for word.")
        elif cited:
            lines.append("<b>Number check:</b> passed. Every number in the answer is in the cited facts.")
        path = {"answered": "Answered from approved memory only.",
                "restricted": "A fact outside your role matched. Its content was not sent to the model and is not shown here.",
                "pending": "A note on this is still waiting for review, so I didn't use it.",
                "unknown": "Nothing in the approved memory you may see answers this, so: “I don't know”."}.get(t.get("path"), "")
        if path:
            lines.append(f"<b>Result:</b> {esc(path)}")
        mode = (f"Gemini <span class='ids'>{esc(llm.MODEL)}</span> on Vertex AI" if t.get("mode") == "gemini"
                else "Offline keyword match (no model call)")
        lines.append(f"<b>Mode:</b> {mode}")
        for n in t.get("notes") or []:
            lines.append(esc(n))
        md("<div class='how'>" + "".join(f"<div>{x}</div>" for x in lines) + "</div>")


def brief_row(it: dict, user: str, scope: str, i: int) -> None:
    with rise(scope, i):
        if it.get("security"):
            md(f"<div class='row blocked'><div class='when high'>Blocked</div><div class='txt'>{esc(it['text'])}</div></div>")
        else:
            u = it.get("urgency", "medium")
            md(f"<div class='row'><div class='when {u}'>{WHEN.get(u, 'This week')}</div><div class='txt'>{esc(it['text'])}</div></div>")
        sources_block(it.get("cited", []), user)


def kind_label(a: dict) -> str:
    """Who an action goes to, in words: 'message colleague to Giulia Ferrero', 'announcement to Winery customers (24)'."""
    if a["type"] == "announcement":
        return f"announcement to {store.label(a['to'])}"
    if a["type"] == "zoom_meeting":
        m = a.get("meeting", {})
        return "Zoom meeting with " + ", ".join(store.label(i) for i in m.get("with", [a["to"]]))
    if a["type"] == "notion_update":
        return f"page update: {store.label(a['to'])}"
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


# ---------- memory page: decisions with reasons, conflicts, receipts, edits, history ----------
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
    ss.decide = None


def is_editing(m: dict) -> bool:
    return ss.get("editing") == {"id": m["id"], "status": m["status"]}


def toggle_decide(item_id: str, kind: str) -> None:
    target = {"id": item_id, "kind": kind}
    ss.decide = None if ss.get("decide") == target else target
    ss.editing = None


def deciding(item_id: str, kind: str) -> bool:
    return ss.get("decide") == {"id": item_id, "kind": kind}


def do_mem_approve(mid: str, user: str) -> None:
    try:
        memory.approve(mid, user)
        flash("pending", "success", f"{mid} is approved. Jarvis can use it from now on.")
    except (PermissionError, ValueError) as e:
        flash("pending", "error", str(e))
    except KeyError:
        flash("pending", "error", "That item no longer exists.")


def decide_form(m: dict, user: str, kind: str, old: list | None = None) -> None:
    """Reasons (graft from builds/daddy): a rejection, or an approval despite a warning, needs a short written reason (kept in the audit log)."""
    mid = m["id"]
    prompt = {"reject": "Why reject it?", "approve": "Why approve it anyway?",
              "replace": f"Why replace {', '.join(old or [])}?"}[kind]
    label = {"reject": "Confirm reject", "approve": "Confirm approve", "replace": "Confirm replace"}[kind]
    with st.container(key=f"decidebox-{kind}-{mid}"):
        with st.form(f"decide-{kind}-{mid}", border=False, clear_on_submit=False):
            fa, fb = st.columns([4, 1.4], vertical_alignment="bottom")
            reason = fa.text_input(prompt, key=f"reason-{kind}-{mid}", max_chars=300,
                                   placeholder="One short line. It is saved with the decision and in the audit log.")
            go = fb.form_submit_button(label, key=f"confirm-{kind}-{mid}", type="primary", width="stretch")
        if go:
            try:
                if kind == "reject":
                    memory.reject(mid, user, reason)
                    flash("pending", "success", f"{mid} rejected. It stays in History with your reason; Jarvis never uses it.")
                elif kind == "approve":
                    memory.approve(mid, user, reason=reason)
                    flash("pending", "success", f"{mid} approved with your reason on record.")
                else:
                    memory.approve(mid, user, supersede=old, reason=reason)
                    flash("pending", "success", f"{mid} is approved. {', '.join(old or [])} is no longer used and stays in History.")
            except (PermissionError, ValueError) as e:
                st.error(str(e), icon=":material/error:")
                return
            except KeyError:
                st.error("That item no longer exists.", icon=":material/error:")
                return
            ss.decide = None
            st.rerun()


def conflict_block(m: dict, found: list) -> None:
    """New vs approved now, side by side, in amber. Jarvis keeps answering from the approved fact until a person chooses."""
    now = "".join(f"<div class='cf-side now'><div class='cf-k'>Approved now · <span class='ids cy'>{c['id']}</span></div>"
                  f"<div>{esc(c['fact'])}</div><div class='cf-why'>{esc(c['why'] or 'Different values')}</div></div>"
                  for c in found)
    md(f"<div class='row conflict'><div class='when medium'>Conflict</div><div class='txt'>"
       f"<div class='cf-grid'><div class='cf-side new'><div class='cf-k'>New · <span class='ids cy'>{m['id']}</span></div>"
       f"<div>{esc(m['fact'])}</div></div><div class='cf-stack'>{now}</div></div>"
       "<div class='cf-note'>Both can't be true. Jarvis keeps using the approved fact until a person chooses.</div></div></div>")


def receipt_block(r: dict) -> None:
    """Decision receipt (graft from builds/uluhan): which fact is active, which was rejected or replaced, by whom, when, on which source."""
    def fact(e: dict, tag: str) -> str:
        srcs = " · ".join(f"<span class='ids cy'>{esc(s['id'])}</span> <span class='ids'>{esc(s['kind'])}, {esc(s['date'])}</span>"
                          for s in e["sources"]) or "<span class='ids'>no source you can see</span>"
        by = f" · approved by {esc(e['approved_by'])}" if e.get("approved_by") and tag == "Active" else ""
        return (f"<div class='rc-side {'on' if tag == 'Active' else 'off'}'><div class='cf-k'>{tag} · <span class='ids cy'>{esc(e['id'])}</span>"
                f"<span class='ids'>{by}</span></div><div>{esc(e['fact'])}</div><div class='rc-src'>Source: {srcs}</div></div>")
    verb = {"replaced": "Replaced", "rejected": "Rejected", "blocked": "Blocked"}[r["outcome"]]
    gone = "".join(fact(e, verb) for e in r["out"])
    act = "".join(fact(e, "Active") for e in r["active"]) or "<div class='rc-side'><div class='who'>No approved fact on this topic now.</div></div>"
    why = f"<div class='rc-why'><b>Reason:</b> {esc(r['reason'])}</div>" if r.get("reason") else ""
    md(f"<div class='receipt'><div class='rc-head'><span class='when {'low' if r['outcome'] == 'replaced' else 'medium'}'>{verb}</span>"
       f"<span class='rc-who'>by {esc(r['by'])}" + (f" · {stamp(r['at'])}" if stamp(r['at']) else "") + "</span></div>"
       f"<div class='cf-grid'><div class='cf-stack'>{act}</div><div class='cf-stack'>{gone}</div></div>{why}</div>")


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
                flash(f"item:{mid}", "success", f"Edit saved. {mid} still needs approval before Jarvis uses it.")
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
        bits.append(f"by {esc(name(who))}" + (f" · {stamp(when)}" if stamp(when) else ""))
    if m["status"] == "rejected" and m.get("reason"):
        bits.append(f"reason: {esc(m['reason'])}")
    return str(when or ""), (f"<div class='row past'><div class='when past'>{label}</div><div class='txt'><s>{esc(m['fact'])}</s>"
                             f"<span class='ids'>{' · '.join(bits)}</span></div></div>")


def do_act_approve(aid: str, user: str) -> None:
    try:
        propose.approve_action(aid, user)
    except (PermissionError, ValueError, KeyError) as e:
        ss.act_flash = {"id": aid, "msg": str(e)}


# ---------- sidebar ----------
with st.sidebar:
    md(f"<div class='wordmark'>{MARK}<b>JARVIS</b></div><div class='wordmark-sub'>for <span class='co'>{esc(store.short_name())}</span>"
       " · speaks first, asks before it acts</div>")
    st.selectbox("Signed in as", list(PEOPLE), key="user", format_func=lambda u: f"{PEOPLE[u]['name']} · {PEOPLE[u]['role']}")
    st.caption("Access: " + ", ".join(g for g in access.groups(ss.user) if g != "all") + ". Set here, never by what you type.")
    st.radio("Go to", PAGES, key="page", label_visibility="collapsed")

    md("<div class='side-h'>Demo controls</div>")
    st.button("Run the 08:00 sweep", icon=":material/schedule:", on_click=do_sweep, width="stretch",
              help="Jarvis writes everyone's brief and proposes actions, without anyone asking (live Gemini)")
    @st.fragment(run_every=60)
    def auto_sweep() -> None:
        """Graft (builds/daddy): the morning sweep runs by itself every JARVIS_SWEEP_MINUTES (default 30)."""
        if brief.maybe_sweep():
            st.rerun(scope="app")
        nxt = brief.minutes_to_next_sweep()
        if nxt is not None:
            st.caption(f"Next automatic sweep in {nxt} min (every {brief.sweep_interval_minutes()} min while the app is open).")

    auto_sweep()
    if is_ceo(ss.user):
        st.button("Reset the demo", icon=":material/restart_alt:", on_click=do_reset, width="stretch",
                  help="CEO only: back to the 08:00 state")
    st.button("New email arrives", icon=":material/mark_email_unread:", on_click=do_new_email, width="stretch")
    st.button("An URGENT email arrives", icon=":material/notification_important:", on_click=do_urgent_email, width="stretch",
              help="Jarvis decides it's urgent, calls the CEO with a spoken briefing, and prepares a fix that waits for approval")
    if ss.get("last_watch", {}).get("status") == "already received":
        st.warning("Jarvis already handled this email: it calls only once per email. The CEO can **Reset the demo** to replay it.",
                   icon=":material/info:")
    with st.expander("Paste an email · try to break Jarvis", icon=":material/shield:"):
        ex = store.demo_events().get("examples", {})
        e1, e2, e3 = st.columns(3)
        for col, key, lab in ((e1, "ceo_fraud", "CEO fraud"), (e2, "reworded_injection", "Injection"), (e3, "normal", "Normal")):
            if key in ex:
                col.button(lab, key=f"ex-{key}", on_click=lambda k=key: ss.update(
                    paste_from=ex[k]["from"], paste_subject=ex[k]["subject"], paste_body=ex[k]["body"]), width="stretch")
        with st.form("paste-email", border=False):
            st.text_input("From", key="paste_from", placeholder="someone@outside.example")
            st.text_input("Subject", key="paste_subject")
            st.text_area("Email", key="paste_body", height=120, placeholder="Write any email, including an attack.")
            if st.form_submit_button("Deliver to me", icon=":material/send:"):
                try:
                    res = watch.paste_email(ss.user, ss.paste_from, ss.paste_subject, ss.paste_body)
                    ss.paste_result = res
                except (ValueError, KeyError) as e:
                    ss.paste_result = {"status": "error", "reasons": [str(e)]}
        pr = ss.get("paste_result")
        if pr:
            if pr.get("status") == "flagged":
                st.error("Blocked: " + "; ".join(pr.get("reasons", [])) + ". No memory, no action, no call.", icon=":material/gpp_bad:")
            elif pr.get("status") == "ingested":
                st.success(f"Read it. New facts wait for review: {', '.join(pr.get('pending', []))}. "
                           + ("Urgent: a call card was raised (pasted emails never ring a real phone)." if pr.get("call") else ""),
                           icon=":material/check_circle:")
            elif pr.get("status") == "error":
                st.warning("; ".join(pr.get("reasons", [])), icon=":material/info:")
    if stripe_sync.can_sync(ss.user) and not stripe_sync.connected():
        st.caption("Stripe is not connected for this company.")
    elif stripe_sync.can_sync(ss.user):
        st.button("Sync Stripe to the revenue page", icon=":material/payments:", key="stripe-sync", on_click=do_stripe_sync,
                  width="stretch", help="Reads Stripe payments, proposes the revenue fact (flagged if approved memory disagrees) "
                                        "and an update to the revenue page. Both wait for approval.")
    sr = ss.get("stripe_result")
    if sr and sr.get("user") == ss.user:
        if sr.get("error"):
            st.error(sr["error"], icon=":material/error:")
        else:
            st.success(f"{sr['origin']}: {sr['net']} from {sr['payments']} payments. "
                       + (f"Conflicts with {', '.join(sr['conflicts'])}: resolve it in Memory. " if sr["conflicts"] else "")
                       + "The page update waits in Approvals.", icon=":material/check_circle:")
            st.button("Review in Memory", key="stripe-go-memory", on_click=goto, args=(PAGES[1],), width="stretch")

    status = check_status()
    md(f"<div class='side-h'>Jury checklist <span class='n'>{sum(status.values())}/7</span></div>")
    for c in DEMO.get("checks", []):
        n, page = c["n"], PAGE_KEYS.get(c.get("page", "today"), PAGES[0])
        user_c = c.get("user") if c.get("user") in PEOPLE else ss.user
        st.button(f"{n}. {c['label']}", key=f"chk{n}", on_click=goto, args=(page, user_c, c.get("question", "")), width="stretch",
                  icon=":material/check_circle:" if status.get(n) else ":material/radio_button_unchecked:",
                  help=f"As {PEOPLE[user_c]['name']}" + (f": “{c['question']}”" if c.get("question") else ""))
    done = ", ".join(f".st-key-chk{n} [data-testid='stIconMaterial']" for n in status if status[n])
    st.html("<style>[class*='st-key-chk'] [data-testid='stIconMaterial']{color:var(--text-3)}"
            + (f"{done}{{color:var(--green)}}" if done else "") + "</style>")
    if DEMO.get("hint"):
        md(f"<div class='chk'>{esc(DEMO['hint'])}</div>")

user = ss.user
me = PEOPLE[user]

# ---------- header ----------
h1, h2 = st.columns([2.7, 1.3])
with h2:
    paused = llm.configured_mode() == "gemini" and llm.breaker_remaining() > 0
    if paused:
        md(f"<div class='status'><span class='led off'></span>Gemini paused after {llm.BREAKER_FAILS} failures · "
           f"offline fallback for <span class='mono'>{llm.breaker_remaining()} s</span></div>")
    elif llm.mode() == "gemini":
        md(f"<div class='status'><span class='led'></span>Gemini <span class='mono'>{llm.MODEL}</span> · Vertex AI</div>")
    else:
        md("<div class='status'><span class='led off'></span>Offline fallback (no Gemini credentials)</div>")

# ---------- incoming call from Jarvis (on-screen phone, real ElevenLabs voice, optional real phone call) ----------
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
           f"<div class='call-meta'>{esc(c['why'])} · source <span class='ids'>{c['source']}</span>{esc(fix_line)}</div></div></div>")

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
                md(f"<div class='script-label'>Jarvis says</div><div class='script'>“{esc(c['script'])}”</div>")
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
        o, g = st.columns([1, 3.5], vertical_alignment="center")   # orb column keeps its width next to the counters
        with o:
            orb(136)
        with g:
            md(f"<div class='greet'>Good morning, {esc(first(user))}.</div>"
               f"<div class='sub'>{NOW.strftime('%A %d %B').replace(' 0', ' ')} · <span class='num'>{len(items)}</span> things need you"
               + (f" · <span class='num wait'>{len(pending)}</span> waiting for your approval" if pending else "") + "</div>")
    with h2:
        cn = tally.counts(user)
        md("<div class='counters'>" + "".join(
            f"<div class='ctr{' wait' if k != 'brief' and cn[k] else ''}'><b>{cn[k]}</b><span>{lab}</span></div>"
            for k, lab in (("brief", "Brief items"), ("review", "To review"), ("actions", "Pending actions"))) + "</div>")

    left = right = st.container()
    with left:
        channels = sorted({s["channel"] for s in access.visible(store.sources(), user) if s["kind"] == "chat"})
        if ss.channel not in ["Jarvis"] + channels:
            ss.channel = "Jarvis"
        st.radio("Workspace", ["Jarvis"] + channels, key="channel", horizontal=True,
                 format_func=lambda c: "Jarvis (direct)" if c == "Jarvis" else c)
    with right:
        if ss.channel != "Jarvis":
            with st.container(key="panel-channel"):
                section(ss.channel, first_in_panel=True)
                msgs = sorted((s for s in access.visible(store.sources(), user) if s.get("channel") == ss.channel), key=lambda s: s["date"])
                for i, s in enumerate(msgs):
                    with rise("ch", i):
                        md(f"<div class='msgline'><div class='who'><b>{esc(name(s['author']))}</b> · "
                           f"<span class='ids'>{s['date'][5:16].replace('T', ' ')}</span></div>"
                           f"<div class='txt'>{esc(s['text'])}</div></div>")
        else:
            with st.container(key="panel-brief"):
                if b.get("alerts"):
                    section("New since 08:00", len(b["alerts"]), first_in_panel=True)
                    for i, it in enumerate(b["alerts"]):
                        brief_row(it, user, "al", i)
                section("Your 08:00 brief", first_in_panel=not b.get("alerts"),
                        note=f"Posted by Jarvis {esc(b.get('posted_at', ''))}. Nobody asked for it.")
                for i, it in enumerate(b["items"]):
                    brief_row(it, user, "br", i)
                bc1, bc3, bc2, _ = st.columns([1.3, 1.3, 1.9, 0.3])
                if voice.available() and b["items"]:
                    bc1.button("Play my brief", key="brief-play", icon=":material/volume_up:", on_click=do_play_brief, args=(user,), width="stretch")
                if b["items"]:
                    bc3.button("Talk to Jarvis", key="brief-talk", icon=":material/mic:", on_click=do_talk, args=(user,), width="stretch",
                               help="A live voice chat with Jarvis about your own brief. Approvals stay in the app.")
                if pending:
                    bc2.button(f"Review {len(pending)} waiting for approval", icon=":material/task_alt:", on_click=goto, args=(PAGES[2],), width="stretch")
                vcs = ss.get("voice_chat")
                if vcs and vcs.get("user") == user and b["items"]:
                    if vcs.get("session") is None:
                        try:
                            with st.spinner("Opening a voice line to Jarvis…"):
                                vcs["session"] = phone.web_session(user)
                        except Exception:  # web_session never raises; belt and braces
                            vcs["session"] = {"ok": False, "message": phone.UNAVAILABLE}
                    sess = vcs["session"]
                    if sess.get("ok"):
                        voice_chat(sess["signed_url"], sess["dynamic_variables"])
                    else:
                        st.info(sess.get("message") or phone.UNAVAILABLE, icon=":material/mic_off:")
                    t1, t2, _ = st.columns([1.3, 1.1, 2.6])
                    t1.button("New voice chat", key="talk-retry", icon=":material/refresh:", on_click=do_talk, args=(user,), width="stretch")
                    t2.button("Close", key="talk-close", icon=":material/close:", on_click=do_close_talk, width="stretch")
                bv = ss.get("brief_voice")
                if bv and bv.get("user") == user and voice.available() and b["items"]:
                    text = f"Good morning {first(user)}. " + " ".join(i["text"] for i in b["items"])
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
                        md(f"<div class='q'>{esc(qa['question'])}</div>"
                           f"<div class='a{'' if qa['known'] else ' unknown'}'>{esc(qa['answer'])}</div>")
                        sources_block([c["mem_id"] for c in qa["citations"]], user)
                        how_block(qa)
                chips = tally.chip_questions(DEMO)
                if chips:
                    with st.container(key="chips", horizontal=True, gap="small"):
                        for i, cq in enumerate(chips):
                            st.button(cq, key=f"chip-{i}", on_click=do_chip, args=(cq,), width="content",
                                      help="Ask this now, as the person signed in")
                with st.form("ask", clear_on_submit=True, border=False):
                    fq, fb = st.columns([5, 1])
                    q = fq.text_input("Ask Jarvis", value=ss.prefill, placeholder=DEMO.get("ask_placeholder", "Ask about the team's work"),
                                      label_visibility="collapsed")
                    if fb.form_submit_button("Ask", type="primary", width="stretch") and q.strip():
                        do_ask(user, q)
                        st.rerun()

elif ss.page == PAGES[1]:
    with h1:
        md("<div class='greet'>Team memory</div><div class='sub'>Jarvis answers only from approved items. Each item keeps the access list of its source.</div>")
    groups = store.company().get("groups", {})
    with st.container(key="panel-note"):
        section("Add what you know", first_in_panel=True,
                note="Knowledge that isn't in email, chat or docs. It's approved by you when it's your area; otherwise its owner reviews it. It's cited as your note.")
        with st.form("add-note", clear_on_submit=True, border=False):
            note_text = st.text_area("What should Jarvis know?", key="note-text", max_chars=500, height=96,
                                     placeholder=DEMO.get("note_placeholder", ""))
            na, nb = st.columns([3, 1.2], vertical_alignment="bottom")
            note_acl = na.multiselect("Who can see it", memory.shareable_groups(user), default=["all"], key="note-acl",
                                      format_func=lambda g: f"{g} · {groups.get(g, g)}")
            saved = nb.form_submit_button("Save to memory", icon=":material/add_task:", type="primary", width="stretch")
        if saved:
            try:
                item = memory.add_manual(user, note_text, note_acl)
                if item["status"] == "pending" and item.get("conflicts"):
                    ids = [c["id"] for c in memory.conflicts(item["id"], user)]
                    st.warning(f"Your note contradicts {', '.join(ids) if ids else 'approved memory'}, so it went to review "
                               f"instead of being saved directly. Resolve {item['id']} below.", icon=":material/warning:")
                elif item["status"] == "pending":
                    who = ", ".join(name(r) for r in memory.reviewers(item["id"]))
                    st.info(f"Saved as {item['id']}. It's outside your area, so {who} reviews it before Jarvis uses it.",
                            icon=":material/hourglass_top:")
                else:
                    st.success(f"Saved as {item['id']}, approved by you and cited as {', '.join(item['sources'])}.", icon=":material/check_circle:")
            except (ValueError, PermissionError) as e:
                st.error(str(e), icon=":material/error:")
    ov = store.company().get("overview", {})
    mem_all = access.visible(store.memory(), user)
    with st.container(key="panel-overview"):
        section(f"About {store.short_name()}", first_in_panel=True)
        md(f"<div class='ov'><div class='txt'>{esc(ov.get('about', store.company().get('company', {}).get('what', '')))}</div>"
           f"<div class='who' style='margin-top:.6rem'><b>Offer:</b> {esc(' · '.join(ov.get('offer', [])))}</div>"
           f"<div class='who'><b>How it works:</b> {esc(' · '.join(ov.get('how', [])))}</div>"
           f"<div class='who'><b>Team:</b> {esc(' · '.join(p['name'] + ' (' + p['role'] + ')' for p in PEOPLE.values()))}</div>"
           f"<div class='who'><b>Jarvis reads:</b> {esc(' · '.join(ov.get('tools', [])))} · {esc(ov.get('where', ''))}</div>"
           f"<div class='who'><b>Who decides:</b> {esc(store.company().get('approval_rule', ''))}</div>"
           f"<div class='who'><b>Memory you can see:</b> {sum(m['status'] == 'approved' for m in mem_all)} approved · "
           f"{sum(m['status'] == 'pending' for m in mem_all)} waiting for review · "
           f"{sum(m['status'] in ('superseded', 'rejected') for m in mem_all)} in history</div></div>")
        data = memory.export(user) if ss.get("export_ready") else None
        d1, d2, _ = st.columns([1.3, 1.3, 2.4])
        if data is None:
            d1.button("Prepare export", key="export-prepare", icon=":material/download:", width="stretch",
                      on_click=lambda: ss.update(export_ready=True))
        else:
            day = data["exported_at"][:10]
            base = re.sub(r"[^A-Za-z0-9]+", "-", store.short_name()).strip("-").lower()
            d1.download_button("Download (Markdown)", memory.export_markdown(data), file_name=f"{base}-memory-{day}.md",
                               mime="text/markdown", key="export-md", icon=":material/description:", width="stretch")
            d2.download_button("Download (JSON)", json.dumps(data, indent=2, ensure_ascii=False), file_name=f"{base}-memory-{day}.json",
                               mime="application/json", key="export-json", icon=":material/data_object:", width="stretch")
        md("<div class='who'>The export holds only what your role may see, with sources and who approved each fact.</div>")
    fl = ss.pop("mem_flash", None)
    pend = memory.pending_for(user)
    with st.container(key="panel-pending"):
        section("Waiting for review", len(pend), first_in_panel=True)
        show_flash("pending", fl)
        if not pend:
            md("<div class='empty'>Nothing to review that you can see. New facts appear here when an email arrives.</div>")
        for i, m in enumerate(pend):
            found = memory.conflicts(m["id"], user)
            warns = memory.number_warnings(m)
            mine = memory.can_review(m["id"], user)
            deciders = ", ".join(name(r) + " (" + PEOPLE[r]["role"] + ")" for r in memory.reviewers(m["id"])) or "the CEO"
            with rise("mp", i):
                edited = f" · edited by {esc(first(m['edited_by']))}" if m.get("edited_by") else ""
                md(f"<div class='row'><div class='when medium'>Pending</div><div class='txt'>{esc(m['fact'])}"
                   f"<span class='ids'>{m['id']} · proposed by {esc(m.get('proposed_by', 'extractor'))}{edited} · visible to {', '.join(m['acl'])}</span>"
                   + (f"<div class='quote'>Quote from the source: “{esc(m['quote'])}”</div>" if m.get("quote") else "")
                   + f"<div class='who'>Who can decide: {esc(deciders)}</div>"
                   + "".join(f"<div class='warn'>{esc(w)}</div>" for w in warns) + "</div></div>")
                sources_block(m["sources"], user)
                if found:
                    conflict_block(m, found)
                old = [c["id"] for c in found]
                blocked = memory.older_source_block(m["id"], old) if found else None
                if blocked:
                    md(f"<div class='blockmsg'>{esc(blocked)}</div>")
                if mine:
                    if found:
                        c1, c2, c3, _ = st.columns([2.3, 1, 1, 2.2])
                        c1.button(f"Approve and replace {', '.join(old)}", key=f"sup-{m['id']}", icon=":material/swap_horiz:",
                                  type="primary", disabled=bool(blocked), width="stretch",
                                  help=blocked or "Asks for a short reason, then retires the approved fact (kept in History).",
                                  on_click=toggle_decide, args=(m["id"], "replace"))
                    elif warns:
                        c1, c2, c3, _ = st.columns([1.6, 1, 1, 2.4])
                        c1.button("Approve anyway", key=f"apw-{m['id']}", icon=":material/check:", width="stretch",
                                  help="The number check found a problem: write why you approve it anyway.",
                                  on_click=toggle_decide, args=(m["id"], "approve"))
                    else:
                        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
                        c1.button("Approve", key=f"ap-{m['id']}", icon=":material/check:", type="primary",
                                  on_click=do_mem_approve, args=(m["id"], user), width="stretch")
                    c2.button("Reject", key=f"rj-{m['id']}", icon=":material/close:", width="stretch",
                              on_click=toggle_decide, args=(m["id"], "reject"))
                else:
                    md(f"<div class='who'>You can see this, but only {esc(deciders)} can approve or reject it.</div>")
                    c3, _ = st.columns([1, 5])
                c3.button("Close" if is_editing(m) else "Edit", key=f"edt-{m['id']}", icon=":material/close:" if is_editing(m) else ":material/edit:",
                          on_click=toggle_edit, args=(m["id"], m["status"]), width="stretch")
                for kind in ("reject", "approve", "replace"):
                    if mine and deciding(m["id"], kind):
                        decide_form(m, user, kind, old)
                if is_editing(m):
                    edit_form(m, user, groups)
                show_flash(f"item:{m['id']}", fl)
    recs = memory.receipts(user)
    with st.container(key="panel-receipts"):
        section("Decision receipts", len(recs), first_in_panel=True,
                note="When two facts disagree, a person decides. Each receipt shows which fact is active, which one lost, who decided, when, and on which source.")
        if not recs:
            md("<div class='empty'>No conflict decided yet. Try mem-p03: its source is older than the approved budget.</div>")
        for i, r in enumerate(recs[:4]):
            with rise("rc", i):
                receipt_block(r)
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
                by = f" · approved by {esc(name(m['approved_by']))}" if m.get("approved_by") else ""
                t.markdown(f"<div class='msgline'><div class='txt'>{esc(m['fact'])}</div>"
                           f"<span class='ids'>{m['id']} · {', '.join(m['sources'])}{origin}{by}</span></div>", unsafe_allow_html=True)
                if memory.can_review(m["id"], user):
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
    af = ss.pop("act_flash", None)
    with h1:
        md(f"<div class='greet'>Approvals</div><div class='sub'><span class='num{' wait' if waiting else ''}'>{len(waiting)}</span> waiting. "
           "Jarvis has no tool that sends: nothing leaves until you approve it.</div>")
    with st.container(key="panel-actions"):
        section("Proposed by Jarvis", len(acts), first_in_panel=True)
        if not acts:
            md("<div class='empty'>Nothing proposed for you.</div>")
        for i, a in enumerate(acts):
            label = {"awaiting_approval": ("Waiting", "medium"), "approved": ("Sent", "low"), "rejected": ("Rejected", "high"),
                     "needs_review": ("Needs review", "high")}[a["status"]]
            with rise("ac", i):
                md(f"<div class='row'><div class='when {label[1]}'>{label[0]}</div><div class='txt'><b>{esc(a['subject'])}</b>"
                   f"<div class='who'>{esc(kind_label(a))} · why: {esc(a['reason'])}</div>"
                   f"<div class='body'>{esc(a['body'])}</div>"
                   + (f"<div class='who' style='margin-top:.4rem'>Join: <span class='ids'>{esc(a['meeting']['join_url'])}</span>"
                      + ("" if a["meeting"].get("real") else " (demo link)") + "</div>"
                      if a.get("meeting", {}).get("join_url") else "")
                   + (f"<div class='who' style='margin-top:.4rem'>Rejected by {esc(name(a['decided_by']))}: {esc(a['reason_decided'])}</div>"
                      if a["status"] == "rejected" and a.get("reason_decided") else "")
                   + "</div></div>")
                sources_block(a["cites"], user)
                if af and af["id"] == a["id"]:
                    st.error(af["msg"], icon=":material/error:")
                if a.get("edited_by"):
                    md(f"<div class='who'>Edited by {esc(name(a['edited_by']))} before approval.</div>")
                if a["status"] == "needs_review":
                    st.warning("This draft relied on " + ", ".join(
                        f"{s['id']} ({'replaced by ' + s['replaced_by'] if s.get('replaced_by') else s['status']})" for s in a.get("stale", []))
                        + ", which changed after it was written. Edit it (or reject it) before it can be sent.", icon=":material/history:")
                if a["status"] in ("awaiting_approval", "needs_review"):
                    sc = propose.self_check(a["id"], user)
                    if sc["status"] == "warnings":
                        md("<div class='selfcheck warn-amber'><b>Self-check:</b> not supported by the cited sources: "
                           + "; ".join(f"“{esc(x)}”" for x in sc["items"]) + ". You decide.</div>")
                    elif sc["status"] == "ok":
                        md("<div class='selfcheck'>Self-check: every statement is supported by the cited sources.</div>")
                    elif sc["status"] == "offline":
                        md("<div class='selfcheck'>Self-check needs Gemini (offline now). Read the draft against its sources.</div>")
                    c1, c2, c3, _ = st.columns([1.4, 1, 1.1, 1.5])
                    c1.button("Approve and send", key=f"aa-{a['id']}", icon=":material/send:", type="primary",
                              on_click=do_act_approve, args=(a["id"], user), width="stretch")
                    c2.button("Reject", key=f"ar-{a['id']}", icon=":material/close:", width="stretch",
                              on_click=toggle_decide, args=(a["id"], "act-reject"))
                    editing = ss.get("edit_action") == a["id"]
                    c3.button("Close" if editing else "Edit draft", key=f"aedit-{a['id']}", icon=":material/close:" if editing else ":material/edit:",
                              on_click=lambda aid=a["id"], e=editing: ss.update(edit_action=None if e else aid, decide=None), width="stretch")
                    if deciding(a["id"], "act-reject"):
                        with st.container(key=f"decidebox-act-{a['id']}"):
                            with st.form(f"areject-{a['id']}", border=False):
                                ra, rb = st.columns([4, 1.4], vertical_alignment="bottom")
                                why = ra.text_input("Why reject it?", key=f"areason-{a['id']}", max_chars=300,
                                                    placeholder="One short line. It is saved with the decision and in the audit log.")
                                if rb.form_submit_button("Confirm reject", key=f"aconfirm-{a['id']}", type="primary", width="stretch"):
                                    try:
                                        propose.reject_action(a["id"], user, why)
                                        ss.decide = None
                                        st.rerun()
                                    except (ValueError, PermissionError) as e:
                                        st.error(str(e), icon=":material/error:")
                    if editing:
                        with st.form(f"aform-{a['id']}", border=False):
                            subj = st.text_input("Subject", value=a["subject"], key=f"aform-subj-{a['id']}")
                            body = st.text_area("Message", value=a["body"], height=180, key=f"aform-body-{a['id']}")
                            if st.form_submit_button("Save draft", type="primary"):
                                try:
                                    propose.edit_action(a["id"], user, subj, body)
                                    ss.edit_action = None
                                    st.rerun()
                                except (ValueError, PermissionError) as e:
                                    st.error(str(e), icon=":material/error:")
    box = propose.outbox_for(user)
    with st.container(key="panel-outbox"):
        section("Team outbox", len(box), first_in_panel=True,
                note="Mock: nothing leaves this demo. You see an approved item only if you may see every source it cites.")
        for i, o in enumerate(box):
            with rise("ob", i):
                md(f"<div class='msgline'><div class='txt'><b>{esc(o['subject'])}</b> to {esc(store.label(o['to']))}</div>"
                   f"<span class='ids'>approved by {esc(name(o['decided_by']))} at {o['decided_at'][11:16]}"
                   + (f" · {esc(o['sent'])}" if o.get("type") == "zoom_meeting" else "") + "</span></div>")

elif ss.page == PAGES[3]:
    mark_viewed("email")
    b = store.briefs().get(user, {"items": []})
    items = b.get("alerts", []) + b["items"]
    with h1:
        md("<div class='greet'>Morning email</div><div class='sub'>Where the team meets Jarvis at 08:00, before opening anything else.</div>")
    lis = "".join(f"<li>{esc(i['text'])} <span class='ids'>[{', '.join(i.get('cited', []))}]</span></li>" for i in items)
    n_pending = sum(a["status"] == "awaiting_approval" for a in propose.for_user(user))
    sender = store.company().get("company", {}).get("mail_from", "jarvis@company.example")
    md(f"""<div class="mail hud-panel"><div class="meta"><span>From Jarvis <span class="mono">&lt;{esc(sender)}&gt;</span></span><span>To {esc(me['name'])}</span><span>{NOW.strftime('%A %d %B').replace(' 0', ' ')}, <span class="mono">08:00</span></span></div>
<h3>Good morning {esc(first(user))}: {len(items)} things need you today</h3><ol>{lis}</ol>
<p><b>{n_pending} waiting for your approval.</b> Nothing is sent until you approve it in Jarvis.</p>
<p class="who">Every item cites its source. Jarvis only uses memory your team approved and that your role may see. Mock-up: no real email is sent.</p></div>""")

else:
    with h1:
        md("<div class='greet'>Audit log</div><div class='sub'>Everything Jarvis did: who asked, what it cited, what it proposed, who approved, and why."
           + ("" if is_ceo(user) else " You see your own events and system events about items your role may see; the CEO sees all.") + "</div>")
    # Role filter on the log too: a log row can carry fact text, so it follows the same access rules as the memory.
    mem_by = {m["id"]: m for m in store.memory()}
    src_by = store.source_by_id()

    def row_visible(r: dict) -> bool:
        if is_ceo(user) or r.get("user") == user:
            return True
        if r.get("user") is not None:   # someone else's question, approval or note: theirs, not yours
            return False
        refs = [r.get(k) for k in ("mem_id", "source") if r.get(k)]
        refs = [x for x in refs if isinstance(x, str)]
        if not refs:
            return r.get("event") in ("sweep",)
        return all(access.can_see(mem_by.get(x) or src_by.get(x) or {"acl": []}, user) for x in refs)

    # every cell as text: some events log one id, others a list or a count, and mixed column types break the table
    rows = [{k: ", ".join(map(str, v)) if isinstance(v, list) else (None if v is None else str(v)) for k, v in r.items()}
            for r in reversed(audit.read()) if row_visible(r)]
    st.dataframe(rows, width="stretch", height=460)
    u = llm.USAGE
    if u["calls"]:
        st.caption(f"This session: {u['calls']} Gemini calls, {u['input_tokens']} input + {u['output_tokens']} output tokens ≈ ${llm.cost_eur_estimate():.4f} at list price.")

# ---------- nav badges: drawn last, so they count what is true after this run's approvals and rejections ----------
# Same role filter as the pages: Memory = pending items this person may decide; Approvals = drafts waiting for them.
# (No badge for Morning email: there is no per-person "unread" state for it.) Zero: no badge.
_badges = {2: tally.to_review(user), 3: tally.pending_actions(user)}
with st.sidebar:
    st.html("<style>" + "".join(
        f".st-key-page [role='radiogroup'] > :nth-child({n}) label[data-testid='stRadioOption'] [data-testid='stMarkdownContainer'] p::after"
        f"{{content:'{c}';display:inline-block}}" for n, c in _badges.items() if c) + "</style>")
