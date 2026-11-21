# CHECKS.md: Hamid's build (`builds/daddy`)

**Run:** `python builds/daddy/app.py` → http://localhost:8020 (no install). Tests: `python -m unittest discover -s builds/daddy/tests -v`

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

**What I'm proudest of / worth grafting:**
- Zero dependencies: `python app.py` and it runs, even with no Wi-Fi or credits (offline mode, clearly labelled).
- The answer tells apart **I don't know**, **not for your role (ask Giulia)**, and **a note exists but no person approved it yet**, without sending any restricted content to the model.
- Human in the loop on every write: memory, emails and tasks. The approver can **edit the draft** before approving, and every decision with its reason is in the audit log.
- Proposal guards against leaks and exfiltration (internal recipients must be allowed to see the sources; external recipients must be the sender of a cited email).

**Known gaps:**
- Not yet run against live Gemini here (no credentials on this laptop); the REST client follows the Vertex `generateContent` API.
- Offline Q&A is strict keyword matching: an unusual phrasing gets "I don't know".
- Identity is a picker, not a login.
