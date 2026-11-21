"""Jarvis for Filare Labs: Arif's build of Challenge A (Company Jarvis). Run: python -m streamlit run app.py"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from brain import access, answer, audit, brief, llm, memory, propose, store, voice, watch  # noqa: E402

st.set_page_config(page_title="Jarvis · Filare Labs", page_icon="🎩", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
.msg {border:1px solid #2e3648; border-radius:12px; padding:14px 16px; margin:8px 0; background:#161b26;}
.msg .who {font-weight:700;} .msg .meta {color:#8b95a8; font-size:0.82rem; margin-left:6px;}
.item {margin:6px 0 2px 0;} .high {color:#ff8f6b;} .medium {color:#f2c14e;} .low {color:#8bd3a5;}
.chip {display:inline-block; font-size:0.75rem; padding:1px 8px; border-radius:999px; background:#26304a; color:#c9d4ea; margin-right:4px;}
.pill {display:inline-block; font-size:0.78rem; padding:2px 10px; border-radius:999px; background:#26304a; margin-bottom:6px;}
.ok {background:#1d3b2b; color:#8bd3a5;} .warn {background:#3b2f14; color:#f2c14e;}
.mail {background:#fbfaf6; color:#1b1f2a; border-radius:12px; padding:24px 28px; max-width:720px;}
.mail h3 {color:#1b1f2a; margin-top:0;} .mail .muted {color:#5a6275; font-size:0.9rem;}
</style>""", unsafe_allow_html=True)

PEOPLE = store.people()
PAGES = ["🎩 Jarvis", "🗂️ Memory review", "✅ Approvals", "📧 Morning email", "📜 Audit log"]
ss = st.session_state
ss.setdefault("user", "davide")
ss.setdefault("page", PAGES[0])
ss.setdefault("prefill", "")
ss.setdefault("chat", {})
ss.setdefault("channel", "🎩 Jarvis")

if not store.briefs():
    if store.has_snapshot():
        store.restore_snapshot()
    else:
        with st.spinner("Jarvis is running its 08:00 sweep for everyone…"):
            brief.sweep()


# ---------- helpers ----------
def name(uid: str) -> str:
    p = PEOPLE.get(uid)
    return p["name"] if p else uid


def goto(page: str, user: str | None = None, prefill: str = "") -> None:
    ss.page = page
    if user:
        ss.user = user
    ss.prefill = prefill
    ss.channel = "🎩 Jarvis"


def do_reset() -> None:
    """Instant: restores the 08:00 briefs Jarvis made earlier. '▶ 08:00 sweep' regenerates them live."""
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


def norm(q: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", q.lower()).strip()


def check_status() -> dict:
    rows = audit.read()
    asks = [r for r in rows if r["event"] == "ask"]
    approved = {r["mem_id"] for r in rows if r["event"] == "memory_approved"}
    s = {
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
    return s


def mark_viewed(page: str) -> None:
    key = f"viewed-{page}"
    if not ss.get(key):
        ss[key] = True
        audit.log("viewed", ss.user, page=page)


def render_cites(ids: list, user: str) -> None:
    mem = {m["id"]: m for m in access.visible(store.memory(), user)}
    src = {s["id"]: s for s in access.visible(store.sources(), user)}
    for cid in ids:
        if cid in mem:
            m = mem[cid]
            with st.expander(f"📎 memory {cid} · {m['status']}"):
                st.write(m["fact"])
                for sid in m["sources"]:
                    if sid in src:
                        s = src[sid]
                        st.caption(f"{s['kind']} {sid} · {s.get('author', '')} · {s['date'][:16]}")
                        st.write(f"**{s['title']}**: {s['text']}")
        elif cid in src:
            s = src[cid]
            with st.expander(f"📎 {s['kind']} {cid}"):
                st.caption(f"{s.get('author', '')} · {s['date'][:16]}")
                st.write(f"**{s['title']}**: {s['text']}")


# ---------- sidebar ----------
with st.sidebar:
    st.markdown("### 🎩 Jarvis · Filare Labs")
    if llm.mode() == "gemini":
        st.markdown(f'<span class="pill ok">Gemini {llm.MODEL} · Vertex AI {llm.LOCATION}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill warn">Offline fallback · no Gemini credentials</span>', unsafe_allow_html=True)
    st.selectbox("You are", list(PEOPLE), key="user", format_func=lambda u: f"{PEOPLE[u]['name']} · {PEOPLE[u]['role']}")
    st.caption("Groups: " + ", ".join(access.groups(ss.user)) + ". Identity comes from here, never from what you type.")
    st.radio("Go to", PAGES, key="page")
    c1, c2 = st.columns(2)
    c1.button("▶ 08:00 sweep", on_click=do_sweep, width="stretch", help="Jarvis writes everyone's brief and proposes actions, without anyone asking")
    c2.button("↺ Reset demo", on_click=do_reset, width="stretch")
    st.button("📨 Simulate: a new email arrives", on_click=do_new_email, width="stretch")

    st.markdown("---\n#### Jury checklist")
    status = check_status()
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
        st.button(f"{'✅' if status[n] else '⬜'} {n}. {label}", key=f"chk{n}", on_click=goto, args=(page, user, q), width="stretch")
    st.caption(f"{sum(status.values())}/7 shown since the last reset. "
               "3: ask the runway as Giulia, then switch to Sara and ask again. 2: approve mem-p01, reject mem-p02, then ask.")

user = ss.user
me = PEOPLE[user]

# ---------- pages ----------
if ss.page == PAGES[0]:
    mark_viewed("brain")
    left, right = st.columns([1, 3])
    with left:
        st.markdown("**Filare Labs**")
        channels = sorted({s["channel"] for s in access.visible(store.sources(), user) if s["kind"] == "chat"})
        st.radio("Channels", ["🎩 Jarvis"] + channels, key="channel", label_visibility="collapsed")
    with right:
        if ss.channel != "🎩 Jarvis":
            st.markdown(f"#### {ss.channel}")
            for s in sorted((s for s in access.visible(store.sources(), user) if s.get("channel") == ss.channel), key=lambda s: s["date"]):
                st.markdown(f'<div class="msg"><span class="who">{html.escape(name(s["author"]))}</span>'
                            f'<span class="meta">{s["date"][5:16].replace("T", " ")}</span><br>{html.escape(s["text"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"#### 🎩 Jarvis → {me['name']}")
            b = store.briefs().get(user, {"items": []})
            for title, items in (("New since your brief", b.get("alerts", [])), (f"Good morning {me['name'].split()[0]}. Here's what needs you today.", b["items"])):
                if not items:
                    continue
                st.markdown(f'<div class="msg"><span class="who">🎩 Jarvis</span><span class="meta">{b.get("posted_at", "")} · nobody asked · {b.get("mode", "")}</span>'
                            f'<br><b>{html.escape(title)}</b></div>', unsafe_allow_html=True)
                for i, it in enumerate(items, 1):
                    st.markdown(f'<div class="item"><span class="{it.get("urgency", "medium")}">●</span> {html.escape(it["text"])}</div>', unsafe_allow_html=True)
                    render_cites(it.get("cited", []), user)
            if voice.available() and b["items"]:
                if st.button("🔊 Play my brief (ElevenLabs)"):
                    text = f"Good morning {me['name'].split()[0]}. " + " ".join(i["text"] for i in b["items"])
                    try:
                        st.audio(voice.speak(user, text), format="audio/mpeg")
                    except Exception as e:  # never crash the demo
                        st.warning(f"Voice unavailable: {e}")
            pending = [a for a in propose.for_user(user) if a["status"] == "awaiting_approval"]
            if pending:
                st.info(f"✋ {len(pending)} action(s) are waiting for your approval. Nothing is sent until you approve.")
                st.button("Review them", on_click=goto, args=(PAGES[2],))

            for qa in ss.chat.get(user, []):
                st.markdown(f'<div class="msg"><span class="who">{html.escape(me["name"])}</span><br>{html.escape(qa["question"])}</div>', unsafe_allow_html=True)
                cls = "" if qa["known"] else "warn"
                st.markdown(f'<div class="msg"><span class="who">🎩 Jarvis</span><span class="meta">{qa["mode"]}</span><br>'
                            f'<span class="{cls}">{html.escape(qa["answer"])}</span></div>', unsafe_allow_html=True)
                render_cites([c["mem_id"] for c in qa["citations"]], user)

            with st.form("ask", clear_on_submit=True):
                q = st.text_input("Ask Jarvis", value=ss.prefill, placeholder="e.g. When does the Langhe fix roll out?")
                if st.form_submit_button("Ask") and q.strip():
                    ss.chat.setdefault(user, []).append(answer.ask(user, q))
                    ss.prefill = ""
                    st.rerun()

elif ss.page == PAGES[1]:
    st.markdown("#### 🗂️ Memory review")
    st.caption("Jarvis answers **only** from approved memory. Each item keeps the access list of its source, so people only see what their team may see.")
    pend = memory.pending_for(user)
    if not pend:
        st.write("Nothing waiting for review that you can see.")
    for m in pend:
        with st.container(border=True):
            st.markdown(f"**{m['id']}** · proposed by {m.get('proposed_by', 'extractor')} · visible to: {', '.join(m['acl'])}")
            st.write(m["fact"])
            render_cites(m["sources"], user)
            c1, c2 = st.columns(2)
            c1.button("✅ Approve", key=f"ap-{m['id']}", on_click=memory.approve, args=(m["id"], user), width="stretch")
            c2.button("❌ Reject", key=f"rj-{m['id']}", on_click=memory.reject, args=(m["id"], user), width="stretch")
    vis = access.visible(store.memory(), user)
    with st.expander(f"Approved memory you can see ({sum(m['status'] == 'approved' for m in vis)})"):
        for m in vis:
            if m["status"] == "approved":
                st.markdown(f"- **{m['id']}** {m['fact']}")
    rej = [m for m in vis if m["status"] == "rejected"]
    if rej:
        with st.expander(f"Rejected ({len(rej)}): never used for answers"):
            for m in rej:
                st.markdown(f"- ~~{m['fact']}~~ · rejected by {name(m.get('reviewed_by', ''))}")

elif ss.page == PAGES[2]:
    st.markdown("#### ✅ Approvals")
    st.caption("Jarvis has no tool that sends. It only proposes. An action moves to the outbox only when **you** click Approve. "
               "Recipients are checked in code: colleagues, or the original sender of a normal email. Suspicious emails never lead to an action.")
    acts = propose.for_user(user)
    if not acts:
        st.write("No actions proposed for you.")
    for a in acts:
        with st.container(border=True):
            st.markdown(f"**{a['subject']}** · {a['type'].replace('_', ' ')} → **{html.escape(name(a['to']))}** · status: `{a['status']}`")
            st.write(a["body"])
            st.caption(f"Why: {a['reason']}")
            render_cites(a["cites"], user)
            if a["status"] == "awaiting_approval":
                c1, c2 = st.columns(2)
                c1.button("✅ Approve and send (mock)", key=f"aa-{a['id']}", on_click=propose.approve_action, args=(a["id"], user), width="stretch")
                c2.button("❌ Reject", key=f"ar-{a['id']}", on_click=propose.reject_action, args=(a["id"], user), width="stretch")
    box = [o for o in store.outbox() if o["proposed_to"] == user]
    st.markdown(f"##### 📤 Outbox ({len(box)})")
    for o in box:
        st.markdown(f"- **{o['subject']}** → {name(o['to'])} · approved by {name(o['decided_by'])} at {o['decided_at'][11:16]} · {o['sent']}")

elif ss.page == PAGES[3]:
    mark_viewed("email")
    b = store.briefs().get(user, {"items": []})
    items = b.get("alerts", []) + b["items"]
    lis = "".join(f"<li style='margin-bottom:8px'>{html.escape(i['text'])} <span class='muted'>[{', '.join(i.get('cited', []))}]</span></li>" for i in items)
    n_pending = sum(a["status"] == "awaiting_approval" for a in propose.for_user(user))
    st.markdown(f"""<div class="mail"><div class="muted">From: Jarvis &lt;jarvis@filare-labs.example&gt; · To: {html.escape(me['name'])} · Mon 23 Nov, 08:00</div>
<h3>Good morning {html.escape(me['name'].split()[0])}: {len(items)} things need you today</h3><ol>{lis}</ol>
<p><b>{n_pending} action(s) wait for your approval.</b> Nothing is sent until you approve it in Jarvis.</p>
<p class="muted">Every item cites its source. Jarvis only uses memory your team approved and that your role may see. (Mock-up: no real email is sent.)</p></div>""",
                unsafe_allow_html=True)

else:
    st.markdown("#### 📜 Audit log")
    st.caption("Everything Jarvis did: who asked, what it answered and cited, what it proposed, and who approved.")
    rows = list(reversed(audit.read()))
    st.dataframe(rows, width="stretch", height=460)
    u = llm.USAGE
    if u["calls"]:
        st.caption(f"This session: {u['calls']} Gemini calls, {u['input_tokens']} input + {u['output_tokens']} output tokens ≈ ${llm.cost_eur_estimate():.4f} at list price.")
