"""Jarvis for Filare Labs: Arif's build of Challenge A (Company Brain).
Run from builds/arif:  .venv\\Scripts\\python -m streamlit run app.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from brain import access, answer, audit, brief, call, llm, memory, propose, store, voice, watch  # noqa: E402

st.set_page_config(page_title="Jarvis · Filare Labs", page_icon=":material/support_agent:", layout="wide")

# Butler's desk: warm paper, ink, one brass accent. Serif for headings, Plex Sans for text, Plex Mono only for source ids.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root { --paper:#F5F0E6; --paper2:#EDE5D5; --sheet:#FBF8F1; --ink:#1E1A14; --ink2:#4E463A; --rule:#D9CEB8;
        --brass:#8A5A12; --brass-tint:#F3E6CB; --red:#A3341F; --red-tint:#F6E1DA; --green:#2F6B47; }
html, body, .stApp { background: var(--paper); color: var(--ink); font-family: 'IBM Plex Sans', system-ui, sans-serif; }
::selection { background: var(--brass-tint); color: var(--ink); }
* { scrollbar-color: var(--rule) transparent; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: var(--paper2); border-right: 1px solid var(--rule); }
.block-container { padding-top: 2.2rem; max-width: 1180px; }
h1, h2, h3, .serif { font-family: 'Newsreader', Georgia, serif !important; letter-spacing: -0.01em; color: var(--ink); }
.wordmark { font-family: 'Newsreader', Georgia, serif; font-size: 2rem; font-weight: 600; line-height: 1; color: var(--ink); }
.wordmark-sub { color: var(--ink2); font-size: .92rem; margin: .25rem 0 1.1rem; }
.greet { font-family: 'Newsreader', Georgia, serif !important; font-size: 2.6rem !important; font-weight: 500; line-height: 1.1; margin: 0; color: var(--ink); text-wrap: balance; }
.sub { color: var(--ink2); font-size: 1rem; margin: .4rem 0 1.6rem; }
.status { font-size: .8rem; color: var(--ink2); text-align: right; padding-top: .6rem; }
.status b { color: var(--green); font-weight: 600; }
.status b.off { color: var(--brass); }
.section { font-family: 'Newsreader', Georgia, serif; font-size: 1.35rem; font-weight: 600; margin: 1.8rem 0 .4rem; }
.row { display: grid; grid-template-columns: 7.5rem 1fr; gap: 1rem; padding: .85rem 0 .35rem; border-top: 1px solid var(--rule); }
.when { font-size: .82rem; font-weight: 600; padding-top: .15rem; }
.when.high { color: var(--red); } .when.medium { color: var(--brass); } .when.low { color: var(--green); }
.txt { font-size: 1.02rem; line-height: 1.5; max-width: 68ch; }
.row.blocked { background: var(--red-tint); border-top-color: #E7C2B7; padding-left: .7rem; padding-right: .7rem; border-radius: 6px; }
.ids { font-family: 'IBM Plex Mono', ui-monospace, monospace; font-size: .78rem; color: var(--ink2); }
.q { font-weight: 600; margin-top: 1.1rem; }
.a { line-height: 1.55; max-width: 68ch; }
.a.unknown { color: var(--brass); }
.who { font-size: .8rem; color: var(--ink2); }
.msgline { padding: .6rem 0; border-top: 1px solid var(--rule); }
.mail { background: var(--sheet); border: 1px solid var(--rule); border-radius: 8px; padding: 2rem 2.4rem; max-width: 46rem;
        box-shadow: 0 6px 24px rgba(30,26,20,.08); }
.mail .meta { color: var(--ink2); font-size: .88rem; border-bottom: 1px solid var(--rule); padding-bottom: .8rem; margin-bottom: 1.2rem; }
.mail li { margin-bottom: .6rem; line-height: 1.5; }
.callcard { background: var(--brass-tint); border: 1px solid #E2C995; border-radius: 8px; padding: 1.1rem 1.3rem .4rem; margin-bottom: 1rem; }
.callcard .t { font-family: 'Newsreader', Georgia, serif; font-size: 1.5rem; font-weight: 600; }
.callcard .script { font-family: 'Newsreader', Georgia, serif; font-size: 1.15rem; line-height: 1.5; margin: .6rem 0; max-width: 62ch; }
.chk { font-size: .82rem; color: var(--ink2); margin-top: .4rem; }
[data-testid="stExpander"] details { border: none; background: transparent; }
[data-testid="stExpander"] summary { padding: .1rem 0; font-size: .82rem; color: var(--ink2); }
[data-testid="stExpander"] summary:hover { color: var(--brass); }
</style>""", unsafe_allow_html=True)

PEOPLE = store.people()
PAGES = [":material/wb_sunny: Today", ":material/inventory_2: Memory", ":material/task_alt: Approvals",
         ":material/mail: Morning email", ":material/receipt_long: Audit log"]
WHEN = {"high": "Today", "medium": "This week", "low": "For info"}
ss = st.session_state
ss.setdefault("user", "davide")
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


# ---------- helpers ----------
def name(uid: str) -> str:
    p = PEOPLE.get(uid)
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
    if store.has_snapshot():
        store.restore_snapshot()
    else:
        store.reset_demo()
        brief.sweep()


def do_sweep() -> None:
    brief.sweep()


def do_new_email() -> None:
    ss.last_watch = watch.new_email_arrives()


def do_urgent_email() -> None:
    ss.last_watch = watch.new_email_arrives(watch.URGENT_EMAIL)
    if ss.last_watch.get("call"):
        ss.user = next((c["to"] for c in store.calls() if c["id"] == ss.last_watch["call"]), ss.user)
        ss.page = PAGES[0]


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


def sources_block(ids: list, user: str) -> None:
    """Every claim shows where it came from: memory item → original email, chat, task or doc."""
    if not ids:
        return
    mem = {m["id"]: m for m in access.visible(store.memory(), user)}
    src = {s["id"]: s for s in access.visible(store.sources(), user)}
    with st.expander(f"Sources · {', '.join(ids)}"):
        for cid in ids:
            if cid in mem:
                m = mem[cid]
                st.markdown(f"<span class='ids'>{cid} · memory · {m['status']}</span>", unsafe_allow_html=True)
                st.write(m["fact"])
                for sid in m["sources"]:
                    if sid in src:
                        s = src[sid]
                        st.markdown(f"<span class='ids'>{sid} · {s['kind']} · {html.escape(str(s.get('author', '')))} · {s['date'][:10]}</span>", unsafe_allow_html=True)
                        st.write(f"**{s['title']}**: {s['text']}")
            elif cid in src:
                s = src[cid]
                st.markdown(f"<span class='ids'>{cid} · {s['kind']} · {html.escape(str(s.get('author', '')))} · {s['date'][:10]}</span>", unsafe_allow_html=True)
                st.write(f"**{s['title']}**: {s['text']}")


def brief_row(it: dict, user: str) -> None:
    if it.get("security") or it["text"].startswith("⚠️"):
        st.markdown(f"<div class='row blocked'><div class='when high'>Blocked</div><div class='txt'>{html.escape(clean(it['text']))}</div></div>",
                    unsafe_allow_html=True)
    else:
        u = it.get("urgency", "medium")
        st.markdown(f"<div class='row'><div class='when {u}'>{WHEN.get(u, 'This week')}</div><div class='txt'>{html.escape(clean(it['text']))}</div></div>",
                    unsafe_allow_html=True)
    sources_block(it.get("cited", []), user)


# ---------- sidebar ----------
with st.sidebar:
    st.markdown("<div class='wordmark'>Jarvis</div><div class='wordmark-sub'>for Filare Labs · speaks first, asks before it acts</div>",
                unsafe_allow_html=True)
    st.selectbox("Signed in as", list(PEOPLE), key="user", format_func=lambda u: f"{PEOPLE[u]['name']} · {PEOPLE[u]['role']}")
    st.caption("Access: " + ", ".join(g for g in access.groups(ss.user) if g != "all") + ". Set here, never by what you type.")
    st.radio("Go to", PAGES, key="page", label_visibility="collapsed")

    st.markdown("<div class='section' style='font-size:1.05rem'>Demo controls</div>", unsafe_allow_html=True)
    st.button("Run the 08:00 sweep", icon=":material/schedule:", on_click=do_sweep, width="stretch",
              help="Jarvis writes everyone's brief and proposes actions, without anyone asking (live Gemini)")
    st.button("Reset the demo", icon=":material/restart_alt:", on_click=do_reset, width="stretch")
    st.button("New email arrives", icon=":material/mark_email_unread:", on_click=do_new_email, width="stretch")
    st.button("An URGENT email arrives", icon=":material/notification_important:", on_click=do_urgent_email, width="stretch",
              help="Jarvis decides it's urgent, phones the CEO with a spoken briefing, and prepares a fix that waits for approval")

    status = check_status()
    st.markdown(f"<div class='section' style='font-size:1.05rem'>Jury checklist · {sum(status.values())} of 7</div>", unsafe_allow_html=True)
    checks = [
        (1, "It speaks first", PAGES[0], "davide", ""),
        (2, "People curate the memory", PAGES[1], "davide", "When does the Langhe fix roll out?"),
        (3, "It knows who's asking", PAGES[0], "giulia", "What is our cash runway?"),
        (4, "It cites", PAGES[0], "giulia", "What is our cash runway?"),
        (5, "It admits gaps", PAGES[0], "sara", "What is the office Wi-Fi password?"),
        (6, "It only proposes", PAGES[2], "luca", ""),
        (7, "It fits the team's day", PAGES[3], "davide", ""),
    ]
    for n, label, page, user, q in checks:
        st.button(f"{n}. {label}", key=f"chk{n}", on_click=goto, args=(page, user, q), width="stretch",
                  icon=":material/check_circle:" if status[n] else ":material/radio_button_unchecked:")
    st.markdown("<div class='chk'>Check 3: ask the runway as Giulia, then as Sara. Check 2: approve mem-p01, reject mem-p02, then ask.</div>",
                unsafe_allow_html=True)

user = ss.user
me = PEOPLE[user]

# ---------- header ----------
h1, h2 = st.columns([3, 1])
with h2:
    if llm.mode() == "gemini":
        st.markdown(f"<div class='status'><b>●</b> Gemini {llm.MODEL} · Vertex AI</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status'><b class='off'>●</b> Offline fallback (no Gemini credentials)</div>", unsafe_allow_html=True)

# ---------- incoming call from Jarvis (mock phone, real ElevenLabs voice) ----------
for c in call.calls_for(user):
    if c["status"] == "ended":
        continue
    ringing = c["status"] == "ringing"
    st.markdown(f"<div class='callcard'><div class='t'>{'Jarvis is calling you' if ringing else 'On the call with Jarvis'}</div>"
                f"<div class='who'>{html.escape(c['why'])} · source <span class='ids'>{c['source']}</span> · "
                "mock phone today; real calls via ElevenLabs Agents + Twilio</div>"
                + ("" if ringing else f"<div class='script'>“{html.escape(c['script'])}”</div>") + "</div>", unsafe_allow_html=True)
    if ringing:
        a1, a2, _ = st.columns([1, 1, 3])
        a1.button("Answer", key=f"ans-{c['id']}", icon=":material/call:", type="primary", on_click=call.answer, args=(c["id"], user), width="stretch")
        a2.button("Decline", key=f"dec-{c['id']}", icon=":material/call_end:", on_click=call.hang_up, args=(c["id"], user), width="stretch")
    else:
        if voice.available():
            try:
                st.audio(voice.speak(f"call-{c['id']}", c["script"]), format="audio/mpeg", autoplay=True)
            except Exception as e:  # never crash the demo
                st.warning(f"Voice unavailable: {e}")
        b1, b2, _ = st.columns([2, 1, 2])
        if c.get("action"):
            b1.button("Review the fix Jarvis prepared", key=f"rev-{c['id']}", icon=":material/task_alt:", type="primary",
                      on_click=goto, args=(PAGES[2],), width="stretch")
        b2.button("Hang up", key=f"hang-{c['id']}", icon=":material/call_end:", on_click=call.hang_up, args=(c["id"], user), width="stretch")

# ---------- pages ----------
if ss.page == PAGES[0]:
    mark_viewed("brain")
    b = store.briefs().get(user, {"items": []})
    items = b.get("alerts", []) + b["items"]
    pending = [a for a in propose.for_user(user) if a["status"] == "awaiting_approval"]
    with h1:
        st.markdown(f"<div class='greet'>Good morning, {html.escape(first(user))}.</div>"
                    f"<div class='sub'>Monday 23 November · {len(items)} things need you"
                    + (f" · {len(pending)} waiting for your approval" if pending else "") + "</div>", unsafe_allow_html=True)

    left, right = st.columns([1, 3.2], gap="large")
    with left:
        channels = sorted({s["channel"] for s in access.visible(store.sources(), user) if s["kind"] == "chat"})
        st.radio("Workspace", ["Jarvis"] + channels, key="channel",
                 format_func=lambda c: "Jarvis (direct)" if c == "Jarvis" else c)
    with right:
        if ss.channel != "Jarvis":
            st.markdown(f"<div class='section' style='margin-top:0'>{html.escape(ss.channel)}</div>", unsafe_allow_html=True)
            for s in sorted((s for s in access.visible(store.sources(), user) if s.get("channel") == ss.channel), key=lambda s: s["date"]):
                st.markdown(f"<div class='msgline'><div class='who'><b>{html.escape(name(s['author']))}</b> · {s['date'][5:16].replace('T', ' ')}</div>"
                            f"<div class='txt'>{html.escape(s['text'])}</div></div>", unsafe_allow_html=True)
        else:
            if b.get("alerts"):
                st.markdown("<div class='section' style='margin-top:0'>New since 08:00</div>", unsafe_allow_html=True)
                for it in b["alerts"]:
                    brief_row(it, user)
            st.markdown(f"<div class='section' style='{'' if b.get('alerts') else 'margin-top:0'}'>Your 08:00 brief</div>"
                        f"<div class='who'>Posted by Jarvis {b.get('posted_at', '')}. Nobody asked for it.</div>", unsafe_allow_html=True)
            for it in b["items"]:
                brief_row(it, user)
            bc1, bc2, _ = st.columns([1.4, 1.6, 2])
            if voice.available() and b["items"] and bc1.button("Play my brief", icon=":material/volume_up:"):
                text = f"Good morning {first(user)}. " + " ".join(clean(i["text"]) for i in b["items"])
                try:
                    st.audio(voice.speak(user, text), format="audio/mpeg", autoplay=True)
                except Exception as e:  # never crash the demo
                    st.warning(f"Voice unavailable: {e}")
            if pending:
                bc2.button(f"Review {len(pending)} waiting for approval", icon=":material/task_alt:", on_click=goto, args=(PAGES[2],))

            st.markdown("<div class='section'>Ask Jarvis</div><div class='who'>Answers come only from team memory you may see, with sources. Otherwise: “I don't know”.</div>",
                        unsafe_allow_html=True)
            for qa in ss.chat.get(user, []):
                st.markdown(f"<div class='q'>{html.escape(qa['question'])}</div>"
                            f"<div class='a{'' if qa['known'] else ' unknown'}'>{html.escape(qa['answer'])}</div>", unsafe_allow_html=True)
                sources_block([c["mem_id"] for c in qa["citations"]], user)
            with st.form("ask", clear_on_submit=True, border=False):
                fq, fb = st.columns([5, 1])
                q = fq.text_input("Ask Jarvis", value=ss.prefill, placeholder="When does the Langhe fix roll out?", label_visibility="collapsed")
                if fb.form_submit_button("Ask", type="primary", width="stretch") and q.strip():
                    ss.chat.setdefault(user, []).append(answer.ask(user, q))
                    ss.prefill = ""
                    st.rerun()

elif ss.page == PAGES[1]:
    with h1:
        st.markdown("<div class='greet'>Team memory</div><div class='sub'>Jarvis answers only from approved items. Each item keeps the access list of its source.</div>",
                    unsafe_allow_html=True)
    pend = memory.pending_for(user)
    st.markdown("<div class='section' style='margin-top:0'>Waiting for your review</div>", unsafe_allow_html=True)
    if not pend:
        st.markdown("<div class='who'>Nothing to review that you can see. New facts appear here when an email arrives.</div>", unsafe_allow_html=True)
    for m in pend:
        st.markdown(f"<div class='row'><div class='when medium'>Pending</div><div class='txt'>{html.escape(m['fact'])}"
                    f"<div class='ids'>{m['id']} · proposed by {m.get('proposed_by', 'extractor')} · visible to {', '.join(m['acl'])}</div></div></div>",
                    unsafe_allow_html=True)
        sources_block(m["sources"], user)
        c1, c2, _ = st.columns([1, 1, 3])
        c1.button("Approve", key=f"ap-{m['id']}", icon=":material/check:", type="primary", on_click=memory.approve, args=(m["id"], user), width="stretch")
        c2.button("Reject", key=f"rj-{m['id']}", icon=":material/close:", on_click=memory.reject, args=(m["id"], user), width="stretch")
    vis = access.visible(store.memory(), user)
    st.markdown(f"<div class='section'>Approved · {sum(m['status'] == 'approved' for m in vis)}</div>", unsafe_allow_html=True)
    for m in vis:
        if m["status"] == "approved":
            st.markdown(f"<div class='msgline'><div class='txt'>{html.escape(m['fact'])}</div><div class='ids'>{m['id']} · {', '.join(m['sources'])}</div></div>",
                        unsafe_allow_html=True)
    rej = [m for m in vis if m["status"] == "rejected"]
    if rej:
        st.markdown(f"<div class='section'>Rejected · never used for answers</div>", unsafe_allow_html=True)
        for m in rej:
            st.markdown(f"<div class='msgline'><div class='txt'><s>{html.escape(m['fact'])}</s></div>"
                        f"<div class='ids'>{m['id']} · rejected by {html.escape(name(m.get('reviewed_by', '')))}</div></div>", unsafe_allow_html=True)

elif ss.page == PAGES[2]:
    acts = propose.for_user(user)
    waiting = [a for a in acts if a["status"] == "awaiting_approval"]
    with h1:
        st.markdown(f"<div class='greet'>Approvals</div><div class='sub'>{len(waiting)} waiting. Jarvis has no tool that sends: nothing leaves until you approve it.</div>",
                    unsafe_allow_html=True)
    if not acts:
        st.markdown("<div class='who'>Nothing proposed for you.</div>", unsafe_allow_html=True)
    for a in acts:
        label = {"awaiting_approval": ("Waiting", "medium"), "approved": ("Sent", "low"), "rejected": ("Rejected", "high")}[a["status"]]
        st.markdown(f"<div class='row'><div class='when {label[1]}'>{label[0]}</div><div class='txt'><b>{html.escape(a['subject'])}</b>"
                    f"<div class='who'>{a['type'].replace('_', ' ')} to {html.escape(name(a['to']))} · why: {html.escape(a['reason'])}</div>"
                    f"<div style='margin-top:.5rem; white-space:pre-line'>{html.escape(a['body'])}</div></div></div>", unsafe_allow_html=True)
        sources_block(a["cites"], user)
        if a["status"] == "awaiting_approval":
            c1, c2, _ = st.columns([1.4, 1, 2.6])
            c1.button("Approve and send", key=f"aa-{a['id']}", icon=":material/send:", type="primary",
                      on_click=propose.approve_action, args=(a["id"], user), width="stretch")
            c2.button("Reject", key=f"ar-{a['id']}", icon=":material/close:", on_click=propose.reject_action, args=(a["id"], user), width="stretch")
    box = [o for o in store.outbox() if o["proposed_to"] == user]
    st.markdown(f"<div class='section'>Outbox · {len(box)}</div><div class='who'>Mock: nothing leaves this demo.</div>", unsafe_allow_html=True)
    for o in box:
        st.markdown(f"<div class='msgline'><div class='txt'><b>{html.escape(o['subject'])}</b> to {html.escape(name(o['to']))}</div>"
                    f"<div class='ids'>approved by {html.escape(name(o['decided_by']))} at {o['decided_at'][11:16]}</div></div>", unsafe_allow_html=True)

elif ss.page == PAGES[3]:
    mark_viewed("email")
    b = store.briefs().get(user, {"items": []})
    items = b.get("alerts", []) + b["items"]
    with h1:
        st.markdown("<div class='greet'>Morning email</div><div class='sub'>Where the team meets Jarvis at 08:00, before opening anything else.</div>",
                    unsafe_allow_html=True)
    lis = "".join(f"<li>{html.escape(clean(i['text']))} <span class='ids'>[{', '.join(i.get('cited', []))}]</span></li>" for i in items)
    n_pending = sum(a["status"] == "awaiting_approval" for a in propose.for_user(user))
    st.markdown(f"""<div class="mail"><div class="meta">From Jarvis &lt;jarvis@filare-labs.example&gt; · to {html.escape(me['name'])} · Monday 23 November, 08:00</div>
<h3 style="margin-top:0">Good morning {html.escape(first(user))}: {len(items)} things need you today</h3><ol>{lis}</ol>
<p><b>{n_pending} waiting for your approval.</b> Nothing is sent until you approve it in Jarvis.</p>
<p class="who">Every item cites its source. Jarvis only uses memory your team approved and that your role may see. Mock-up: no real email is sent.</p></div>""",
                unsafe_allow_html=True)

else:
    with h1:
        st.markdown("<div class='greet'>Audit log</div><div class='sub'>Everything Jarvis did: who asked, what it cited, what it proposed, who approved.</div>",
                    unsafe_allow_html=True)
    rows = list(reversed(audit.read()))
    st.dataframe(rows, width="stretch", height=460)
    u = llm.USAGE
    if u["calls"]:
        st.caption(f"This session: {u['calls']} Gemini calls, {u['input_tokens']} input + {u['output_tokens']} output tokens ≈ ${llm.cost_eur_estimate():.4f} at list price.")
