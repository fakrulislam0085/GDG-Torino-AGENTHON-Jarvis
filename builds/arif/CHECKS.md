# CHECKS.md: Arif's build (Jarvis for PoliPrep)

**Run:** `cd builds\arif; .venv\Scripts\python -m streamlit run app.py` · **Tests:** `.venv\Scripts\python -m pytest tests -q` (33 offline tests)

| # | Check | How it passes (file:function) | Enforced in code? | Steps in the UI |
|---|---|---|---|---|
| 1 | It speaks first | `brief.sweep()` writes everyone's brief (`unprompted: True`); `watch.new_email_arrives()` posts alerts; `call.maybe_call()` rings the CEO's real phone for urgent email | Yes | Arif → Today: the 08:00 brief ("Nobody asked for it"). "An URGENT email arrives" → the phone rings |
| 2 | People curate the memory | `memory.approve/reject/edit`; `answer.ask` uses only `memory.approved_for()`; `memory.conflicts()` flags clashes | Yes | Memory → approve mem-p01, reject (or edit) mem-p02 (conflict "€299 vs €399") → Today → "When is the TOLC-I live this week?" → cites mem-p01. Before approval: "a note is waiting for review" |
| 3 | It knows who's asking | `access.visible()` filters before any model call; `access.can_approve()` checks the owner role | Yes | "What is our Cohort 1 revenue so far?" as Hamid (CFO) → the answer; as Sara (CTO) → "not available for your role, ask Hamid" |
| 4 | It cites | `answer.ask` keeps only ids given to the model; `numbers_supported()` checks every number | Yes | Any answer or brief line → Sources |
| 5 | It admits gaps | `answer.ask` → `why_unknown()`: no approved match, no valid citation, or unsupported numbers → "I don't know" | Yes | "What is the 2027 ARCHED exam date?" → "I don't know" |
| 6 | It only proposes | `propose.py`: no send tool; `approve_action` only by the person proposed to; recipients checked; stale drafts → `needs_review`; Zoom/Notion only after approval | Yes | Hamid → Approvals: the refund reply and the Zoom payment request wait; "Edit draft" then Approve → Outbox |
| 7 | It fits the team's day | Slack-style workspace, morning email, voice brief, **real phone call**, Zoom proposals | n/a | Today, Morning email, the call card |

**Attacks tested (tests/test_checks.py):**
- injection email `email-004`
- a pasted CEO-fraud email
- a reworded injection: caught by Gemini, live
- disguised attacks (look-alike Cyrillic letters, zero-width characters)
- "I'm the CFO" as Sara
- approving someone else's draft
- a non-owner approving finance or company-wide facts
- a pasted urgent email trying to ring the phone
- a stale draft after a fact was replaced

**Worth grafting:**
- the phone call with drafts collected afterwards
- Stripe → Notion with conflict detection
- conflict view + edit + history
- "Paste an email"
- three kinds of "I don't know"
- the memory export
- the voice orb
