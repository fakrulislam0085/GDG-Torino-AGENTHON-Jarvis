# CHECKS.md: the mix (`builds/mafia`)

**Run:** `python builds/mafia/app.py` -> http://localhost:8030. Tests (69): `python -m unittest discover -s builds/mafia/tests -v`. Real browser (40 checks): `python builds/mafia/tests/ui_smoke.py`.

| # | Check | How the mix passes it (file:function) | Code or prompt? | Steps in the UI |
|---|---|---|---|---|
| 1 | It speaks first | `app.py:scheduler` runs `brain.py:Brain.sweep` -> `build_brief` posts each person a brief; `_ingest_spec` posts alerts; `maybe_call` phones the CEO. A brief is only reposted if something changed | Code. The brief is built by code from filtered data; the model writes only the opening line, which is checked | Open Davide's Brain DM: the brief is there. Or pick an event in the header |
| 2 | People curate memory | `Brain.review_memory`; `Brain.ask` reads only `approved`; `extract_candidates` proposes notes (quote-checked, access list copied by code) | Code | As Davide, Memory review: reject mem-p02 (red box), approve mem-p01, then ask "When does the Langhe fix roll out?" |
| 3 | It knows who's asking | `Brain.can_see` before any prompt is built in `Brain.ask`; `open_source` raises 403; calls, meetings and runs are filtered per person | Code | Ask "What is our cash runway?" as Giulia, then as Sara |
| 4 | It cites | `Brain.ask` keeps only cited ids it gave the model, `numbers_ok`, a word-overlap guard; every answer shows its approved fact word for word; chips open the sources | Code (digits and ids; a wrong sentence without digits can pass, hence the verbatim fact) | Click any chip; open the trace of an answer |
| 5 | It admits gaps | `Brain.ask`: no visible approved item or no valid cite gives "I don't know" | Code | Ask "What's the office Wi-Fi password?" |
| 6 | It only proposes | `Brain._add_proposal` (guards) -> `waiting`; `decide_action` only for the named approver; the model has no send tool; the call, the fix and the meeting are proposals | Code | As Luca, Approvals: edit the draft, Outbox is empty, approve. Or answer the CEO's call and approve there |
| 7 | It fits the team's day | `web/index.html`: Brain DM, Morning email, Calls with a call screen, Approvals, voice | n/a | Header and navigation |
| ★ | It phones the CEO (from Arif) | `Brain.maybe_call`, `calls.py`, `phone.py` (optional) | Code: urgency words AND the model agreeing, never for a suspicious email, one call per email, the script may only use numbers from the email | Elena: pick "URGENT: frost tonight", answer the call, approve the fix and the meeting |

**Attacks tested:** the 83,000 note (flagged), "I'm the CFO" as Sara, reworded and look-alike injections (zero-width, Cyrillic, extra whitespace) in the body and the subject, a CEO payment fraud email, an email from an unknown outsider asking for company data, a pasted email with an HTML payload, a pasted sender spoofing a colleague, a note about money from an outsider approved by tech, a forged task proposal, a malformed model proposal in a sweep, a model that invents numbers in the call script, the fix or the alert, a meeting in the past or with an invitee who may not see the email, a call answered by the wrong person, cross-site and oversized requests, spam (cooldown), Reset by a non-CEO.

**Worth grafting / what is new:** the call to the CEO with a fix and a meeting that wait for a click; the agent trace over the Daddy engine; the red-team fixes listed in the README.

**Known gaps:**
- The real phone call, the real Zoom meeting and the ElevenLabs voice are written but not run against real keys here (they fall back and never break an approval).
- Text the model writes is checked for digits and ids only (a number spelled out, or a wrong sentence, can pass); every action still needs a person.
- Identity is a picker, not a login.
- Offline Q&A is strict keyword matching.
- Arif's Stripe-to-Notion sync and Uluhan's change-control receipts were not ported.
