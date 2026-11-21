# Review 1: Jarvis · AGENTHON finalist pitch (Version A and Version B)
Verdict: **FIX AND RE-REVIEW** (both versions)
Counts:
- **Version A:** 2 BLOCKER · 8 MAJOR · 9 MINOR · spoken ≈ 2.5 min (349 words), **≈ 3.3–3.8 min with the live demo and the call** (target 3)
- **Version B:** 1 BLOCKER · 10 MAJOR · 9 MINOR · spoken ≈ 2.5 min (355 words), **≈ 3.3–3.8 min with the live demo and the call** (target 3)

count.py: every slide is under 70 words (largest: slide 05, 52). No fluff words found. The time risk comes from the live demo: count.py counts only the 119 spoken demo words (≈ 51 s), not the clicks, the role switch, the wait for the ring, or Jarvis talking on the phone. The only measured call lasted **101 seconds** (F10).

The skeleton is good. One promise runs through it ("asks before it acts"), there is a real live call, an honest line about market size, and the ask goes to the sponsor. Most fixes are small and factual.

## Headlines alone
1. Jarvis. / The colleague who knows, speaks first, and asks before it acts.
2. A: Every company already has the answer. / It's in someone else's inbox.
   B: A tutor misses tomorrow's class. / Fourteen students don't know yet.
3. It reads everything. / People decide what it remembers.
4. Watch it speak first, say "I don't know", and call me.
5. Rival teams will try to break it. / The rules live in code.
6. Built for one company. / Ready for any firm.
7. Ariete: let's pilot Jarvis with one of your client firms.

→ The story works when you read the headlines alone: problem, how it works, proof live, proof under attack, beyond the prototype, the ask. Every headline is a claim. The headlines are founder-approved, so no headline rewrites are proposed (see "For the founder to decide" for 06). The closing line on slide 07 ("A colleague you trust…") calls back the cover's "colleague". The script does not record its merges and skips (see m8).

Ideas to remember (5, listed in the script): speaks first · only approved memory · says "I don't know" · never acts without a yes, even on the phone · rules in code. They are clear, and the demo shows four of them live.

**Jury rubric (F01) and the 7 checks (F03):**
- Innovation: covered by the phone call in the demo.
- Track fit: covered by the demo.
- Technical execution: covered by slide 05 and the demo. The trace or log is never shown (m6).
- Feasibility: slide 06. "Who pays" and the cost per run are missing from that slide (M4).
- Pitch quality: at risk from the timing (M1).
- The 7 checks: checks 1–5 are clearly shown in the demo. Check 6 (only proposes) is shown only half-way: the action waiting, then the tap, is never closed on screen. Check 7 (fits the team's day) is never named (M6).

## The 8 questions
| Question | Answered on | Status |
|---|---|---|
| 1. What do you do? | 01 (as a metaphor), 03 (plain) | OK. The cover Say could add one plain sentence (m9) |
| 2. How far along? | 05, 06 (built today, demo data, live phone, Stripe and Zoom) | OK |
| 3. How big? | 06 "Market size: not estimated yet" | OK (founder decision) |
| 4. How do you make money / who pays? | Only in qa-prep #10 | **MISSING** on the slides. It is part of the feasibility criterion → M4 |
| 5. Insight | 05 "rules live in code, not in the prompt"; 03 "people decide what it remembers" | OK |
| 6. Team, why them | 07 | A: names only, no "why us". B: strong (the founder lives the problem) |
| 7. Why now? | Nowhere | **MISSING** → M5 |
| 8. The ask | 07 pilot with Ariete | OK, but there is no scope or length (NEED, see "For the founder to decide") |

## Findings
| # | Sev | Ver | Slide | Problem (one line) | Exact fix (replacement text) | Rule |
|---|---|---|---|---|---|---|
| B1 | BLOCKER | A | 02 | "forty sensors", "one email, two chats, one task", "Four people" and "threatens to leave" have no fact ID. The 40-of-120 sensors detail and the renewal threat *are* in the demo data (`builds/best/data_filare/emails.json`, `memory_seed.json` mem-003), but not in facts.md. The other counts are unverified. | **Option 1 (preferred):** add to facts.md: `F21 · Demo data: Cantina Langhe Viva has 40 of 120 sensors offline since 18 Nov; it will pause its renewal if this isn't fixed by 27 Nov · builds/best/data_filare/emails.json, memory_seed.json`. Then keep "forty sensors" and change "threatens to leave" to "may not renew". Confirm "one email, two chats, one task" and "four people" in data_filare (NEED). **Option 2, if they can't be confirmed:** On slide: "One customer: sensors offline, a renewal at risk" / "The answer is spread across email and chat" / "Each person needs to know something different" / "Filare Labs · our demo company". Say: "At Filare Labs, a customer reports sensors offline and may not renew. The email reached sales. The fix is spread across email and chat. Each person needs to know something different, today." | writing-rules §5; Method 1 |
| B2 | BLOCKER | A+B | 06 | "AI hosted in the EU" is not in facts.md, and the repo says the opposite. The demo build runs Gemini on location `global` (`builds/best/.env.example`, `brain/llm.py`, README line 45). The repo is public, so a juror can check. | On slide: "AI runs on Google Vertex AI; finance facts never go to the voice provider". (Say already avoids the EU claim. Keep it that way.) | writing-rules §6; Method 1 |
| M1 | MAJOR | A+B | all | Over time. 349–355 spoken words is about 2.5 min, plus about 45–75 s of demo actions and the call. The only measured call lasted 101 s (F10). | (1) Make Jarvis's spoken opening on the call **two sentences maximum**, and rehearse "What happened?" → "Approve it." until the whole call is under 20 s. (2) Apply the Say cuts in B1/M8, M4 (slide 05 Say → 31 words) and m4. (3) **Cut slide 03 Say to:** "Jarvis reads the team's tools and proposes facts. A person approves them. It answers only from those, with sources. Nothing leaves without a yes." (4) If rehearsal is still over 3:00, drop slide 03 Say completely: the slide and the demo carry it. Time the full run with a stopwatch, demo included. | writing-rules §4; F02 |
| M2 | MAJOR | A+B | 05 | "33 automated tests" and the $0.003 cost come from **builds/arif**, but the demo runs **builds/best**. A juror who reads the public repo could find a different number. | Keep the numbers but label them. Footer: "Our tests and live runs, 21 November 2026 · test count and cost measured on build arif". Or replace them with the builds/best numbers once its agent reports (NEED, already listed in facts.md). | writing-rules §5; F06, F11 |
| M3 | MAJOR | A+B | 05 | "On the phone: 'Approve it' is refused" goes beyond F10. The logged test refused "execute the nuclear missiles" and said approvals are tapped in the app. "Approve it" itself is not in the log. | On slide: "On the phone: no approvals. 'Tap it in the app.'" And **rehearse the exact live line "Approve it" before 17:15**: the demo depends on it. | Method 1; F10 |
| M4 | MAJOR | A+B | 05, 06 | "Who pays" is on no slide, but it is part of the feasibility criterion ("cost per run, who pays…"). The cost per brief sits on 05 instead of under feasibility. | **Slide 05:** delete the row "About $0.003 per morning brief". Add the row "Our 3 attacker agents: all 3 builds still pass 7 of 7" (F07). Say: "Rival teams will try to break it. So the rules live in code, not in the prompt. A reworded attack that our patterns missed was caught by a second AI check." **Slide 06 On slide:** "Already connected: Stripe, Zoom, a real phone line" / "Next: Gmail, Slack, Notion, with the same rules" / "AI runs on Google Vertex AI; finance facts never go to the voice provider" / "About $0.003 per morning brief" / "First buyers: small firms, through partners like Ariete (pilot)" / "Market size: not estimated yet". **Slide 06 Say:** "Stripe, Zoom and a real phone line already work. Gmail, Slack and Notion come next, with the same rules. Finance data never goes to the voice provider. Today, a morning brief costs a third of a cent. The first buyers are small firms, through partners like Ariete. We haven't sized the market yet, and we won't pretend we have." | writing-rules §1 Q4; F01, F11, F14 |
| M5 | MAJOR | A+B | 06 | "Why now" is missing everywhere. | Use the "Today, a morning brief costs a third of a cent." line in M4. It is the only why-now line the facts support. For a stronger one, see NEED under "For the founder to decide". | writing-rules §1 Q7 |
| M6 | MAJOR | A+B | 04 | The jury ticks 7 checks yes or no. Check 6 is never closed (the tap on the waiting action is never shown) and check 7 (where the team meets it) is never named. | Replace the last two sentences of the Say with: "It won't approve by phone. Back in the app, the action waits for one tap. I tap it. Only now does it happen." Change the opening to: "Let me show you. It's eight in the morning. Nobody asked, but each person already has a morning brief, in the app and on the phone." Founder: make the result of the tap visible on screen (for example, the Zoom meeting created after approval, F12). | F03 checks 6–7; audiences.md (rubric beats order) |
| M7 | MAJOR | A+B | 03 vs 06 | Slide 03 says it "Reads email, chat, tasks, docs, Stripe, Zoom", while slide 06 says Gmail, Slack and Notion are "Next". A juror will see the contradiction. Also, Zoom is not *read*: meetings are created after approval (F12). | Slide 03 bullet 1: "Reads email, chat, tasks and docs (demo copies today), and Stripe". Bullet 4: "Drafts actions and Zoom meetings. Nothing happens without a yes." | Method 1; F12, qa-prep #11 |
| M8 | MAJOR | B | 02 | The headline reads like a real event. Facts only support a scenario (F16, F20), and the cohort count is dated 8 Nov. The slide also mixes two problems (sales DMs and the tutor email). | On slide: "PoliPrep: one founder, a few tutors, one media person" / "14 students in Cohort 1. One email in one inbox." / "We demo on Filare Labs: same problem, no real student data". **Delete** "The founder answers about ten sales messages a week himself". Footer: "A typical scenario, not a real incident · PoliPrep internal: team (Oct 2026); Cohort 1 = 14 of 20 places (8 Nov 2026)". | writing-rules §5 (label what isn't a result) |
| M9 | MAJOR | B | 02 → 04 | The seam: the jury hears about a school and a tutor, then watches vineyard sensors and a CFO. The tutor problem is never solved on screen. | Say for slide 02 B: "I run PoliPrep, an admission-test school: one founder, a few tutors, one media person. Picture this: a tutor can't make tomorrow's class. The email sits in one inbox. Fourteen students depend on someone noticing. Today I show it on Filare Labs, a demo company with the same problem: an urgent customer email that landed with sales." | Method 2 (story); F15 |
| M10 | MAJOR | A+B | qa-prep | Some answers are not backed by facts.md. #8 (fallback to rule-based mode): no fact. #6 "decides urgency": no fact. #1 "€299 vs €399": unlabelled example. #7: the cost of a call is unknown. Rival teams may literally test #8 by cutting the network. | #8: add a fact from the build (NEED) or answer: "If Gemini fails, the safety rules still run in code, so nothing gets out. I'll show you." #6: replace "decides urgency" with "flags an urgent email" (only if a fact backs it; NEED). #1: "For example, two prices for the same plan: Jarvis shows both, and the owner decides." #7: "The call cost isn't measured yet." #9: spell out "a data processing agreement (DPA)". | Method 8 |
| m1 | MINOR | A+B (B worse) | 04 | "our CFO / our CTO" sounds like Token Mafia's own team. In B it clashes with "I run PoliPrep". | "Same question about cash runway: Filare's CFO gets the answer. Its CTO gets 'not for your role'." | writing-rules §3 |
| m2 | MINOR | A+B | 07 | "We are three PoliTO builders": the facts make only Hamid and Uluhan PoliTO students (F18). | Say: "I run PoliPrep and Life At PoliTO. Hamid and Uluhan study engineering at PoliTO. We built three versions in parallel and merged the best ideas." (Or add a fact if Arif studies at PoliTO.) | Method 1; F17, F18 |
| m3 | MINOR | A+B | 05 | "7 of 7 jury checks" can sound as if the jury has already marked you. | "All 7 challenge checks, enforced in code" | writing-rules §3 |
| m4 | MINOR | A | 02 | The first Say sentence repeats the headline and "always" overclaims. It costs 13 words. | Delete "In a small company, the important thing is always in someone else's inbox." | writing-rules §3, §4 |
| m5 | MINOR | A+B | 07 | The closing line is hard to say: two quotes joined by a comma. | Closing line and Say: "A colleague you trust says "I don't know." And asks "May I?"" | writing-rules §3 |
| m6 | MINOR | A+B | 04 | The technical-execution criterion asks for the agent trace on screen, and the audit log exists (F08). | Add to the Say after "Blocked.": "Every step is in the log." (Show the log for 2 seconds.) | brief, Judging table |
| m7 | MINOR | A+B | 06 | There is a special prize for "Best use of ElevenLabs", but ElevenLabs is never named. | Slide 06 bullet 1: "Already connected: Stripe, Zoom, a real phone line (ElevenLabs voice over Twilio)" | F10; brief |
| m8 | MINOR | A+B | header | Merges and skips are not stated. | Add under "Ideas to remember": "Spine: Traction = What we built and tested; Business + Market merged into Feasibility; Competition skipped (3 min, covered in Q&A); Team merged with the Ask." | story.md rules |
| m9 | MINOR | A+B | 01 | The cover is a metaphor. A 10-year-old can't yet picture what Jarvis does. | Cover Say: "Hi, I'm Arif, from Token Mafia. This is Jarvis. It reads your team's email and chat, and tells each person what needs them today. And it asks before it acts." | writing-rules §3 (create a picture) |

## Slide scores
| Slide | Clear (1–5) | Proven (1–5) | One-line note |
|---|---|---|---|
| 01 Cover | 4 | – | A strong promise. Add one plain sentence (m9). |
| 02 Problem A | 5 | 2 | A vivid picture that sets up the demo's urgent email. The numbers need a fact line (B1). |
| 02 Problem B | 3 | 3 | Real and credible, but it mixes two problems, isn't labelled as a scenario, and leaves a seam into the demo (M8, M9). |
| 03 Solution | 4 | 3 | Clean. Fix "reads Zoom" and the clash with 06 (M7). |
| 04 Live demo | 5 | 5 | The heart of the pitch. Close check 6 on screen and cap the call length (M6, M1). |
| 05 Built and tested | 4 | 4 | Strong. Label which build the numbers come from and match the phone row to F10 (M2, M3). |
| 06 Feasibility | 3 | 2 | The EU claim is wrong (B2). Who pays and the cost are missing (M4). |
| 07 Team, ask, close | 4 | 4 | Right ask for the sponsor. Add "why us" (A) and the pilot scope (NEED). |

## Questions the jury will ask that qa-prep.md misses
1. **"How is this different from Copilot, Gemini in Workspace or Glean?"** (external jurors). Answer only from our facts, with no claims about them: "Three things you saw live. Memory holds only what a person approved. The role filter runs in code before the model sees anything. And it phones you, but never acts without a tap." (F05, F10, F13)
2. **"Identity is a picker. Can't I just pick CFO?"** qa-prep #11 says "identity is a picker", but F13 says "identity comes from the login". Answer: "In the demo, yes, the picker stands in for a company login. What you type never changes your role. A real login is the first job of the pilot." (Founder: make F13 and #11 agree.)
3. **"Your model runs on 'global'. Does the data leave the EU?"** (GDPR, feasibility). The honest answer depends on a NEED (see below). Don't say "EU".
4. **"Who has time to approve every fact? Won't people stop approving?"** NEED: how many facts per day the demo proposes. Fallback answer: "Only facts that change something are proposed, and each one is a single tap." (Use only if the build does that.)
5. **"What exactly is the pilot? How long, with what data, and what counts as success?"** (the Ariete juror). NEED: pilot terms.
6. **"Does it work in Italian?"** Ariete's clients are Italian SMEs (F14). NEED: test one Italian question before 17:15.
7. **"When does it decide to phone someone? What if it calls at 3 a.m.?"** NEED: the urgency rule in the build.
8. **"What attack are you most worried about? What did your red team almost break?"** A good place to name the weak spot (F07, F08).
9. **(B only) "Do you use Jarvis at PoliPrep today? Did any PoliPrep data go in?"** Answer: "Not yet: today is demo data only, on Filare. PoliPrep would be our own first pilot." (F15)
10. **"How much does one phone call cost?"** qa-prep #7 only says "credits". NEED: the cost per call from the ElevenLabs and Twilio dashboards.

## For the founder to decide
- **Which version.** My recommendation: **Version A, plus one PoliPrep line on slide 07.** A tells one story from start to finish: the customer email on slide 02 is the email that makes your phone ring in the demo. B's real problem is never solved on screen, and with only 3 minutes the context switch costs more than the realness gains. Keep the realness in the team line. A slide 07 Say: "I run PoliPrep, a small school with one founder and a few tutors. I answer about ten sales messages a week myself (F16). I built Jarvis for teams like mine." If you prefer B, apply M8 and M9: they close most of the gap.
- **Sponsor's own words (optional, A or B).** F14 says Ariete's site names the pain "files to open, documents to fill in, deadlines to chase". Quoting it back to the Ariete juror is powerful, but F14 is marked "not re-verified". **Check Ariete's site before you say it.** Also re-check the slide 07 line "Ariete builds AI agents for professional firms", which you'll say to the sponsor's face. If confirmed, A slide 02 Say could end with: "Ariete calls it: files to open, documents to fill in, deadlines to chase."
- **"Ready for any firm" (slide 06 headline)** conflicts with qa-prep #11 ("Is it production-ready? No."). The headline is founder-approved, so it is not counted as a finding. But a juror who hears both answers will notice. Recommendation: "Built for one company. / Ready to pilot with any firm."
- **NEED: the GDPR/region answer.** The demo build runs on `global`. Do you want to state "global endpoint today; a pilot runs in an EU region", and is that possible for this model? (builds/daddy notes that an "eu" multi-region works; that would need a fact line.)
- **NEED: the confirmed counts in the A slide 02 demo data** ("one email, two chats, one task", "four people"), or use Option 2 in B1.
- **NEED: the builds/best test count and cost per brief.** This is already listed in facts.md. Until you have them, keep the "build arif" label (M2).
- **NEED: pilot scope** (one firm, how many weeks, what data, what success means). With it, the ask on slide 07 becomes: "Ariete: let's pilot Jarvis with one of your client firms, for <N> weeks."
- **NEED (optional): a stronger "why now"**, meaning a fact about what changed (cost, voice agents, model quality). Without it, use the cost line in M4.
- **Team name.** The portal shows "Team Islam" and the deck says "Token Mafia" (hackathon-brief.md asks which name the jury sees). Make sure the submission name matches the cover. The pitch order is reverse-alphabetical by project name.
