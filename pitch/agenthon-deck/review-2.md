# Review 2 (final round): Jarvis · AGENTHON finalist pitch (Version A and Version B)
Verdict: **Version A: FIX** · **Version B: FIX**. Each fix below swaps in exact text, so there is no third review. Apply the fixes, rerun count.py, do one timed run with the call, and present.
Counts (BLOCKER and MAJOR only, as asked; MINOR items are not listed):
- **Version A:** 1 BLOCKER · 2 MAJOR · spoken 359 words ≈ 2.6 min, **≈ 3:15–3:30 with the demo clicks and the call** (target 3:00)
- **Version B:** 1 BLOCKER · 2 MAJOR · spoken 370 words ≈ 2.6 min, **≈ 3:20–3:35 with the demo clicks and the call** (target 3:00)

count.py: every slide is under 70 words (largest: 05, 62 words). No fluff words found. Spoken words went **up** since round 1 (A 349 → 359, B 355 → 370) because the new slide 06 and slide 04 text is longer.

## Round 1: what was fixed
| R1 # | Status | Note |
|---|---|---|
| B1 (A 02 numbers) | Fixed | F21 added. "forty sensors", "may not renew" and "reached sales" all match F21. |
| B2 (EU claim) | Fixed | "AI runs on Google Vertex AI" on 06 and in qa #9. |
| M1 (time) | **Open** | See R2. |
| M2 (build label) | Fixed | Footers on 05 and 06 say "build arif". |
| M3 (phone row) | Fixed | The row now matches F10. The phone prompt in `builds/best/brain/phone.py` (lines 5, 40) also refuses a spoken "approve it", so the live line is backed. |
| M4 (who pays, cost) | Fixed | |
| M5 (why now) | Fixed (weak, accepted) | 06: "Today, a morning brief costs a third of a cent." |
| M6 (checks 6–7) | Fixed, but it brought in R1 | Check 6 is now closed on screen. My round-1 wording "and on the phone" was wrong: see R1. |
| M7 (03 vs 06) | Fixed | |
| M8, M9 (B 02 label and seam) | Fixed | |
| M10 (qa-prep backing) | Fixed, one new problem | #8 is backed by the build (`app.py` "Offline fallback", `brain/answer.py`). #6 is backed by `brain/call.py`. #13 is new and unsourced: see R3. |

## Headlines alone
Unchanged and founder-approved. They still tell the whole story: problem → how it works → live proof → proof under attack → beyond the prototype → ask, with the "colleague" callback at the close.

## The 8 questions
| Question | Answered on | Status |
|---|---|---|
| What we do | 03 (plain), 01 | OK |
| How far along | 05, 06 | OK |
| How big | 06 "not estimated yet" | OK (founder decision) |
| How we make money / who pays | 06 "First buyers: small firms, through partners like Ariete (pilot)" | OK |
| Insight | 03, 05 "rules live in code" | OK |
| Team, why them | A: 07 · B: 02 + 07 | OK |
| Why now | 06 cost line | OK (weak) |
| The ask | 07 pilot with Ariete | OK (no length or scope yet, see below) |

The 7 checks (F03) are all visible in the slide 04 demo once R1 is applied.

## Findings
| # | Sev | Ver | Slide | Problem (one line) | Exact fix (replacement text) | Rule |
|---|---|---|---|---|---|---|
| R1 | BLOCKER | A+B | 04 Say | "each person already has a morning brief, in the app **and on the phone**" is not in facts.md, and the build says otherwise. The brief is shown and read aloud in the app (`builds/best/app.py` "Play my brief", `brain/voice.py`). The phone only rings for an urgent email (`brain/call.py`). This wording came from my round-1 M6 fix: my error. | Replace the first three sentences with: **"Let me show you. It's eight in the morning. Nobody asked, but each person already has a morning brief."** In the same Say, replace "our CFO gets the answer, our CTO gets" with **"Filare's CFO gets the answer, its CTO gets"**. In B, "our CFO" just after "I run PoliPrep" sounds like PoliPrep's own team. | Method 1 (facts); writing-rules §6 |
| R2 | MAJOR | A+B | 04–07 | Over time. 359 / 370 spoken words. On top of that come about 20–30 s of clicks and role switches, plus the call: a ring and about 3 Jarvis turns of 1–2 sentences each (phone.py line 36), about 25–40 s. The total is about 3:15–3:35, and in this track the jury scores "3 minutes" under pitch quality. | **05 Say:** delete "Rival teams will try to break it." (the headline says it). **06 Say → "Stripe, Zoom and a real phone line already work. Today, a morning brief costs a third of a cent. The first buyers are small firms, through partners like Ariete. We haven't sized the market yet."** (Gmail/Slack/Notion and the voice-provider line stay on the slide.) **07 Say:** delete "We are three PoliTO builders." (This also fixes round-1 m2: facts.md doesn't say Arif studies at PoliTO.) With R1, that makes **A ≈ 316 and B ≈ 327 words, ≈ 2:15–2:20 spoken**, which leaves about 40–45 s for the demo. Then do one full stopwatch run with the real call. If it is still over 3:00, delete the slide 03 Say (24 words). | writing-rules §4; F02 |
| R3 | MAJOR | A+B | qa-prep #13 | "They search everything you can access and answer." This is a claim about Copilot and Glean with no fact behind it. A juror from GDG or Google can dispute it on the spot, and F05 covers only Jarvis. | Answer: **"I won't speak for their products. Here's what you saw live: memory holds only what a person approved. The role filter runs in code before the model sees anything. And it phones you, but never acts without a tap."** Fact IDs: F05, F10, F13. | writing-rules §6; Method 8 |

No other BLOCKER or MAJOR. Slides 01, 02 (A and B), 03, 05, 06 and 07 match facts.md.

## Slide scores (after the fixes above)
| Slide | Clear | Proven | Note |
|---|---|---|---|
| 01 Cover | 4 | – | OK |
| 02 A | 5 | 5 | Fully sourced (F15, F21) |
| 02 B | 4 | 4 | Labelled as a scenario; the bridge to Filare works |
| 03 | 4 | 4 | No contradiction with 06 any more |
| 04 Demo | 5 | 5 | Shows all 7 checks once R1 is applied |
| 05 | 4 | 5 | Labelled by build |
| 06 | 4 | 4 | Who pays, cost and honest market line |
| 07 | 4 | 4 | Right ask; scope still open |

## Questions the jury will ask that qa-prep.md still misses
1. **"When does it decide to call? What if it's 3 a.m.?"** The build has a rule: it calls only when the model says "urgent" AND the email has clear urgency words (`builds/best/brain/call.py` line 4). Add it to facts.md as F22, then answer: "Only when the model says urgent and the email itself has clear urgency words. It calls the person who has to act." The 3 a.m. part is a NEED.
2. **"What exactly is the pilot?"** (the Ariete juror). NEED: length, data and what success means.
3. **"Who has time to approve every fact?"** NEED: how many facts a day the demo proposes.
4. **(B only) "Did any PoliPrep data go in?"** Answer: "No. Today is demo data only, on Filare. PoliPrep would be our own first pilot." (F15)

## For the founder to decide
- **Before 17:15:** check Ariete's site for the line "Ariete builds AI agents for professional firms" (07). You will say it to the sponsor's face, and F14 is marked "not re-verified".
- **Test count:** `builds/best/tests/test_checks.py` has 47 test functions. I counted them, but I didn't run them. If `pytest` passes on builds/best, change 05 to that number with the footer "build best". Until then, keep "33 · build arif".
- **F13 in facts.md** says "identity comes from the login", but the build uses a picker (qa #11, #14). Suggested F13 wording: "identity comes from the selected user (a stand-in for a company login), never from what is typed."
- **06 headline "Ready for any firm"** versus qa #11 "production-ready? No." The headline is approved and is not counted as a finding. My recommendation is still "Ready to pilot with any firm."
- **Which version:** both are fine once fixed. My recommendation is still A: one story from the email on 02 to the call on 04. B is the better choice if you want the jury to hear that you live the problem.
- **Team name:** the portal says "Team Islam" and the cover says "Token Mafia". Make them match.
