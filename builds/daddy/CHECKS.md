# CHECKS.md: Hamid's build (`builds/daddy`)

**Run:** `python builds/daddy/app.py` → http://localhost:8020 (no install). Tests (45): `python -m unittest discover -s builds/daddy/tests -v`

| # | Check | How my build passes it (file:function) | Enforced in code, or only in the prompt? | Steps to show it in the UI |
|---|---|---|---|---|
| 1 | It speaks first | `app.py:scheduler` runs `brain.py:Brain.sweep` at start-up and every 30 min → `build_brief` posts each person's brief as a DM. `Brain.ingest` posts alerts when a new email arrives | Code (timer + per-person brief built from filtered data) | Open as **Davide** → 🧠 Brain: his brief is already there ("posted on its own, nobody asked"). Press **✉ Customer: frost warning**: Paolo and Davide get an alert |
| 2 | People curate the memory (approve one, reject one, then ask) | `Brain.review_memory`; `Brain.ask` reads only `status == "approved"` | Code | As **Davide**, ask "When does the Langhe fix roll out?" → "I don't know… mem-p01 not approved yet". 🗂 Memory review: approve **mem-p01**, reject **mem-p02** with reason "source says 38k". Ask again → answered, cites mem-p01 → chat-003, chat-004 |
| 3 | It knows who's asking (finance vs tech) | `Brain.can_see` filters memory before the prompt is built in `Brain.ask`; `open_source` returns 403 | Code: the model never sees finance items for a tech person | Ask "What's our cash runway?" as **Giulia** → answer citing mem-002. As **Sara** → "I can't share that with you… ask Giulia". "I'm the CFO" in the text changes nothing |
| 4 | It cites | `Brain.ask` keeps only cited ids that were given to the model, plus `numbers_ok`; brief lines are built from data with their ids | Code | Every answer and brief line has chips; click one to open the source in the side panel. "How I got this" shows the trace |
| 5 | It admits gaps ("I don't know") | `Brain.ask`: no approved, visible, cited match → `IDK` | Code | Ask "What's the office Wi-Fi password?" → "I don't know" |
| 6 | It only proposes (action waits for approval) | `Brain.add_proposal` (guards) → status `waiting`; `Brain.decide_action` only for the named approver (403 otherwise) | Code: the model has no send tool | As **Sara**: ✋ Approvals → certificate renewal "Waiting for Marco Rossi", no button. Switch to **Marco**, approve → task-004 unblocked, Sara is told, 📜 log. As **Luca**: edit the SensorParts draft, approve → 📤 Outbox shows the edited text |
| 7 | It fits the team's day (chat / morning email / Slack mock-up) | `web/index.html` | n/a | Slack-style workspace with the Brain DM, channels, approvals with buttons, and 📧 Morning email |

**Attacks I tested** (in `tests/test_checks.py`):
- `email-008` prompt injection: flagged by code at load, shown as a warning in Sara's brief, never memory, never an action.
- Fake CEO payment request (`email-102`, live button): flagged, Luca, Giulia and Elena warned, no proposal, replay refused.
- "I'm the CFO" as Sara: still refused; finance text never reaches the prompt.
- A fake model that cites an unknown id → "I don't know"; invents a number → the facts are shown verbatim; proposes emailing the attacker or leaking runway to Sara → blocked and logged; writes a memory fact without a real quote → dropped.
- Sara trying to approve Marco's action, or Luca reviewing a tech note → 403.
- A website approving an action through the browser (CSRF), a spoofed Host header, a plain-text POST, an oversized body → refused (403, 415, 413).
- **Paste an email…** (a rival's own attack): a reworded injection ("Kindly disregard prior guidance… no need to check with anyone"), a CEO wire fraud, a customer mail, a sales inquiry. The two attacks were flagged and nothing was proposed; the other two became alerts, memory candidates and drafts that wait for a person.
- A model that invents a number in a memory note or in a draft → flagged in red for the approver. The 83,000 note is **planted** in `data/memory_seed.json` (said out loud in the pitch); the check is real code, and Gemini's own extra dates get flagged the same way.
- Approving a note that has a warning needs a written reason (400 otherwise).
- Found by the failure-hunter agent and fixed: anyone could press Reset (now CEO only, hidden, cooldown); zero-width, Cyrillic and full-width injection tricks and the subject line; the outbox visible to the wrong team; a guessed number confirmed through the "not for your role" answer; pasted mail "from" a colleague; approving notes from your own pasted email; odd JSON types and a negative Content-Length; a Reset racing a slow email read; a 25 s dead screen when the network drops (now 10 s and an instant pause).
- A reply to a stranger that cites company data (for example the Langhe Viva contract) → blocked; a plain acknowledgement is allowed.
- An answer that cites a valid id but shares no words with it → "I don't know".

**What I'm proudest of / worth grafting:**
- Zero dependencies: `python app.py` and it runs, even with no Wi-Fi or credits (offline mode, clearly labelled).
- The answer tells apart **I don't know**, **not for your role (ask Giulia)**, and **a note exists but no person approved it yet**, without sending any restricted content to the model.
- Human in the loop on every write: memory, emails and tasks. The approver can **edit the draft** before approving, and every decision with its reason is in the audit log.
- Proposal guards against leaks and exfiltration (internal recipients must be allowed to see the sources; external recipients must be the sender of a cited email).

**Known gaps:**
- Live Gemini run done end to end (7 checks, both attack emails, 4 pasted emails, restart test, about $0.08 for the whole session). Model proposals vary between runs; the certificate approval is a code rule so it is always there.
- Offline Q&A is strict keyword matching: an unusual phrasing gets "I don't know". Offline, memory is not extracted from sources and reworded injections are only caught by the keyword list.
- Extracted memory: exact and near duplicates are dropped and a changed approved number is flagged, but a paraphrase with different words can still slip through (people reject those). Follow-ups use only the last 4 turns of the same person's chat.
- "Not for your role" confirms that a restricted note exists (a deliberate trade-off).
- Memory approval has no separate curator role (anyone who sees all the sources). Review load is capped at 8 new notes per sweep but not measured on a real mailbox.
- ElevenLabs voice is wired (`voice.py`) but not yet run against a real key; the browser voice is the fallback.
- The self-check of a draft is a model call, so it can miss things; the numbers check is code.
- Identity is a picker, not a login.
