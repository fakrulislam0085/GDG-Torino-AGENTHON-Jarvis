# Red team: compare the 3 solo builds

Run on Sat 21 Nov 2026 with `.claude/workflows/red-team.js` in mode "compare" (run id wf_8d4708ac-e0a). It covered builds/arif, builds/uluhan and builds/daddy (Hamid's build).
- **How it ran:** 3 attackers per build (jury-scorer, devils-advocate, failure-hunter), then 1 referee per build, then 1 verdict. The custom agent types were not registered in this session, so all 9 attackers ran as fallback agents that read the `.claude/agents/*.md` files.
- **Read-only:** static reading only. No app, test or call script was run, and no .env file was opened. Nothing was edited, committed or pushed.
- **Limit:** the agents could not see the UI. Section 5 lists what the live show-off must confirm.

# 14:00 base-build pick: Company Brain (Challenge A)

## 1. Checks matrix

✅ = yes, ❌ = no, ❓ = unclear, 🔒 = enforced in code.

| Build | 1 | 2 | 3 | 4 | 5 | 6 | 7 | Total ✅ | 🔒 | Score /50 |
|---|---|---|---|---|---|---|---|---|---|---|
| Filare Brain (builds/daddy) | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | 7 | 7 | 36 |
| Company Brain (builds/uluhan) | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | 7 | 7 | 31 |
| Jarvis for PoliPrep (builds/arif) | ✅🔒 | ✅🔒 | ✅🔒 | ✅🔒 | ✅ | ✅🔒 | ✅🔒 | 7 | 6 | 31 |

How hard each one is to break:
- **daddy:** no fatal hole. Its worst holes are a role leak when a new email arrives (Gemini mode only) and a reply drafted from a pasted email that the person who pasted it can approve.
- **uluhan:** one fatal hole. A question in a juror's own words gets "I don't know", which can flip checks 2 and 3 to no on stage.
- **arif:** one fatal hole (the README and CHECKS.md describe the wrong company). It also lets any user write company-wide memory, and check 5 relies on the prompt, not on code.

## 2. Recommended base build

**Filare Brain (builds/daddy).**
- Rule 1 is a tie: all three builds pass 7/7.
- Rule 2 picks daddy. It is the only build with no fatal hole, and every one of its checks is enforced in code. uluhan fails on paraphrased questions, and arif lets any user rewrite company-wide facts.
- Rule 3 agrees: daddy scores 36/50 against 31 and 31.
- **How sure:** high. All three pick rules point the same way, so the tie-break is not needed. The only thing that could change this is if the live show-off finds a UI failure the code review could not see.

## 3. Graft list (into builds/daddy, each under 30 minutes)

The referees did not give graft times. The minutes below are my estimates (est.).

| # | What to graft | From | File(s) | Check it fixes | Minutes |
|---|---|---|---|---|---|
| G1 | Make Luca's second-notice review draft a code rule, so it always appears and does not depend on Gemini proposing it. Put it next to `propose_blocked_tasks` in brain.py. | Company Brain (uluhan) | brain/agents.py:`_review_request` | 6 (pitch beat 2 no longer depends on the model) | 15 (est.) |
| G2 | Treat the approved fact as the answer. Gemini only picks which fact; the server prints that fact word for word with its citation. This closes the remaining "wrong sentence with no numbers" gap. | Company Brain (uluhan) | brain/tools.py:`t_answer`, agents.py:`_call_tool` (drops model 'text') | 4 and 5 | 15 (est.) |
| G3 | Use the "nothing left unmatched" rule only on daddy's "not for your role" path: any month, digit or unseen word gives a plain "I don't know". This stops the "Does runway end in June?" oracle. Do NOT graft uluhan's whole matcher, because it refuses too many real questions (its fatal hole). | Company Brain (uluhan) | brain/tools.py:`_confident` (only the digit and rare-word parts) | 3 (against rivals). The same work as daddy's 5-min "restricted words" fix. | 10 (est.) |
| G4 | Withdraw waiting drafts whose cited memory was replaced. Do this only if daddy keeps versions of memory items; check that first. | Company Brain (uluhan) | brain/server.py:`_decide_proposal`, store.py:`replays_current_evidence` | 2 and 6 consistency | 20 (est.) |
| G5 (bonus) | ElevenLabs voice brief button. Send only the person's already-filtered brief text (not arif's call_context, which carries finance), and key the audio cache by a hash of the text. Keep daddy's zero dependencies (use urllib). | uluhan brain/voice.py + server.brief_audio, or arif voice.speak | brain/voice.py, server.brief_audio | None. It adds a bonus to 7 and goes for the ElevenLabs prize. | 25 (est.) |

Not worth grafting: arif's urgent-email phone call. It needs the phone set up, it sends finance memory to ElevenLabs, and it raises safety questions around auto-dial. arif's Streamlit UI does not carry over to daddy's web/index.html. arif's jury checklist adds nothing, because daddy already has `renderChecks`.

## 4. Fix before the 15:30 freeze (builds/daddy)

Minutes and points are the referees'. There are 90 minutes until the freeze. Run the 45 tests after each fix.

**Demo killers first**

| # | Hole | One-line fix | Min | Pts |
|---|---|---|---|---|
| 1 | Saved state (BRAIN_PERSIST on) means mem-p01 is already approved, actions are already decided and the email buttons are disabled. Reset is hidden. | Run with BRAIN_PERSIST=off. Or add step 0 to PITCH.md: `?as=elena&admin=1`, Reset, wait for the briefs, at least 60 s before going on stage. | 3 | 2 |
| 2 | The pitch shows only Sara's refusal, so check 3 can be marked no. | Add a Giulia tab (`?as=giulia&view=brain`). Ask the runway question as Giulia first, then as Sara. | 2 | 2 |
| 3 | Pitch beat 2 (check 6) depends on Gemini proposing the SensorParts draft. Offline there is no red box. | Lead check 6 with the certificate: Sara sees "waiting for Marco", Marco approves. Then do G1 if there is time. | 5 | 1.5 |
| 4 | One badly typed Gemini field (a list, or `cites: null`) aborts the whole sweep or kills the email button. | Wrap `add_proposal` and `_headline` in try/except, reject fields that are not strings, and check `isinstance(cites, list)`. | 10 | 1 |
| 5 | The Gemini location defaults to eu (only global was confirmed). If eu fails, calls fall back to offline quietly and the GDPR line can be false. | Check which auth and location the .env uses, show the live mode before the pitch, and word the GDPR line to match. | 2 | 1 |

**Then most points per minute**

| # | Hole | One-line fix | Min | Pts |
|---|---|---|---|---|
| 6 | No price, and the "half a cent per person per day" cost undercounts. | Add a price per seat per month (needs a number). Recompute the daily cost from the measured $0.0011 per call times the real calls per sweep. | 5 | 1.5 |
| 7 | The Morning email view promises "Reply wrong to any line", which is not built. | Remove the line (index.html:289). | 1 | 0.25 |
| 8 | Identity comes from the picker. | Say on stage: "the picker stands in for Workspace SSO; every call is checked on the server". | 2 | 0.5 |
| 9 | The build only runs from builds/daddy. | Leave it in builds/daddy and point the root README at it. | 2 | 0.5 |
| 10 | Role leak on a new email. The `_ingest_spec` context comes from Elena (readers[0]), so tech and sales sources reach Paolo's and Davide's alert. | Keep only sources every reader can see, and run `unsupported_numbers` on the headline. | 10 | 2 |
| 11 | A reply drafted from a pasted email can leak company data, and the person who pasted it can approve it. | Give unknown outsiders no company context, block unsupported numbers, and refuse `decide_action` from the person who pasted the source. | 15 | 1.5 |
| 12 | The model can name a task's owner as the approver. | For a task with `blocked_by`, force the named approver, and reject approver == owner. | 10 | 1 |
| 13 | Check 2 in Gemini mode may answer loosely before approval. | Return "pending" before the model call when a visible pending note fully matches and no approved note matches. Sort seeded notes first in Memory review. | 10 | 1 |
| 14 | "Not for your role" confirms hidden values through words. | G3 covers it. | 5 | 0.5 |
| 15 | Reworded payment fraud is caught only by the model. | Code flag for IBAN, wire or bank-change requests from unknown senders. | 10 | 0.5 |

**Suggested cut line (90 min):** fixes 1-10 take 42 min. Then fixes 11 and 12 (25 min) and G1 (15 min). That leaves about 8 min of buffer. Cut fixes 13-15 and G2-G5 unless time frees up.

## 5. What the live show-off must confirm (the code review could not see the UI)

- **Check 1:** briefs appear in each DM at start-up without anyone asking, and how long the first brief takes in Gemini mode (the referees say about 20-25 s). The frost email alert reaches the right people only.
- **Check 2:** in Memory review, mem-p01 is visible and Approve and Reject work live. The Langhe question gives "pending" before approval and cites mem-p01 after, in the mode we will pitch in. The 83,000 warning shows, and approving it asks for a written reason.
- **Check 3:** as Giulia and then as Sara, the same runway question gives the answer and then "not for your role". "I'm the CFO" typed in the message changes nothing. Opening a hidden source gives 403.
- **Check 4:** every answer shows the approved fact and opens its source.
- **Check 5:** "What's the office Wi-Fi password?" gives "I don't know" in Gemini mode, not only offline.
- **Check 6:** Approvals shows Sara "waiting for Marco". A wrong-person click is refused without a crash. Marco's approval lands in the mock outbox, and nothing is sent.
- **Check 7:** the Slack-style workspace, the Morning email view, the Audit log (filtered by role) and the Jury checklist all render and turn green.
- **Setup:** the sidebar mode label (live Gemini or offline), which .env auth and location are used, and that Reset leaves a clean state.
- **Grafts:** each graft we add works in the UI.

## 6. The 5 hardest jury or rival questions (builds/daddy)

1. **"I pasted an email as Sara asking for your cloud budget. Why did it draft a reply, and why could Sara approve it?"**
   - Before fix 11: "The outbox is a mock, so nothing leaves." Then admit that only the cited sources are checked today.
   - After fix 11: "A stranger's email gets no company context. Any number not in their own email blocks the draft. The person who pasted it can't approve anything made from it."
2. **"Anyone can pick Giulia in the dropdown. Where is the security?"**
   "The picker stands in for Google Workspace SSO. Every call is checked on the server against that person's groups. The server only accepts calls from its own page on this laptop. Finance memory never enters a tech person's prompt, so typing 'I'm the CFO' changes nothing."
3. **"Who pays, and what does it cost for a 50-person company?"**
   "The owner pays per seat (needs a number). Measured model cost is about $0.0011 per call." Quote the per-person-per-day figure only after fix 6 recomputes it. Do not use "half a cent".
4. **"Brief content is chosen in code. Why is this an agent, not keyword rules?"**
   "Code decides what each person may see and what is safe to say. Gemini does the judgment: it reads the frost email and spots a Wednesday-night frost against a Thursday fix. Code then checks every citation and number before anyone sees it."
5. **"Where does our data go? Is it GDPR-safe?"**
   - Answer only after fix 5 confirms the .env location and auth: "The role filter runs before any model call. The model has no send tool. Every brief, question and approval is in the audit log."
   - Claim "EU region only" only if the .env really uses Vertex in eu. With GOOGLE_API_KEY the global endpoint is used, whatever the location setting.

No files were edited.
