# Token Mafia: AGENTHON winning strategy

We have about 5h45m of real build time (10:15–13:00 and 14:00–17:00), a 3-minute pitch, and a jury that **first picks 8–12 finalists from the written submissions**. So we win twice: first on paper (README, description, video), then on stage (live demo).

## The thesis
**Build one agent that does one real business job end to end, live, with a human approving the risky step.**

Not a chatbot. Not a dashboard. The agent should:
1. **Get a trigger** from the business: an email arrives, a file drops in, a form is submitted, a voice call comes in.
2. **Reason and plan**, and show its plan on screen.
3. **Use 3–5 real tools**: read a doc or sheet, look something up, write a draft, update a record, send for approval.
4. **Stop for human approval** before anything irreversible: send, pay, publish.
5. **Leave an audit trail** that shows each step, each tool call, and what it cost.

That one loop answers four of the five criteria at once: fit (agentic + business), technical quality (real tools, trace), feasibility (approval step, audit, cost), innovation (the job it takes off someone's desk).

## 10:00–10:15: choosing the idea (15 minutes, timeboxed)
Each of us pitches one idea in 60 seconds. Then we score every idea from 1 to 5:

| | Fit with the brief | Wow in the demo | Can we demo end to end by 13:00? | Sponsor's business | Feasibility story |
|---|---|---|---|---|---|

- The idea with the best total wins. **A tie goes to the one we can demo soonest.**
- Ask the sponsor's juror or the organisers one question: *"Who is the business user you have in mind, and what does success look like?"* Write the answer in `hackathon-brief.md`.
- Kill on sight: anything that needs real customer data we don't have, training a model, hardware, or more than 2 external APIs we've never used.

## Roles (confirm at 10:15)
| Role | Owns | Suggested |
|---|---|---|
| **Agent lead** | The agent loop, tools, prompts, Vertex AI and Gemini calls, the trace | _assign_ |
| **Product + UI** | The screen the jury sees: trigger → plan → tool steps → approve → result. Deploy | _assign_ |
| **Story + ship** | The README, the 1000-character description, the deck, the demo video, the ElevenLabs voice, the submission form, and **the clock** | Fakhrul |

Everyone commits to `main` in small commits. Agree the API contract between agent and UI by 10:45 (a JSON shape for steps), so the two can build in parallel.

## Timeline and checkpoints
| Time | Checkpoint | Done when |
|---|---|---|
| 10:15 | Idea locked, roles set, repo cloned by all 3, **GCP credits claimed** | All three have pushed one commit |
| 10:45 | API contract + a skeleton UI with fake data | The UI shows fake steps |
| **12:30** | **Happy path works end to end with real Gemini calls** | We can run the full demo once without help |
| 13:00 | Lunch. Fakhrul drafts the README and the description | |
| 14:00 | Red-team round: run the `jury-scorer`, `devils-advocate` and `failure-hunter` agents | Top 3 fixes chosen |
| 15:00 | ElevenLabs voice layer in (if it fits the idea); polish; deploy | Public link works on a phone |
| **15:30** | **Feature freeze.** Bug fixes only after this | |
| 15:30–16:15 | Deck (5 slides max), record a 60–90 s demo video as backup | Video in the Drive folder |
| 16:15 | Repo **public**, Drive folder shared, submission saved | `final-check` agent passes |
| **16:45** | **Last commit. Nobody pushes after 16:50** | |
| 17:00 | Locked. Rehearse the pitch 3 times with a timer | |

**Rule: if the happy path isn't working by 12:30, we cut scope immediately.** One working flow beats three half-working ones.

## Stack (to use the credits and move fast)
- **Agent:** Gemini on **Vertex AI** (`gemini-3.8-flash`) with function calling, in a region outside Turin (for example `europe-west1` or `us-central1`). Test one call at 10:20.
- **Backend:** Python FastAPI or Node, deployed on **Cloud Run** (covered by the credits) or Vercel.
- **UI:** Vite + React + shadcn, one screen. Show the agent's steps as a live timeline. This is what sells "agentic".
- **Voice (for the ElevenLabs prize):** the agent explains its decision or makes a phone-style call with ElevenLabs TTS or Conversational AI through the API. Only add it if it fits the idea naturally. A gimmick costs points on fit.
- **Building:** we build with Claude Code. Use the `/core:hackathon-kit` routes, `impeccable` for UI polish, and `webapp-testing` to click through like a judge.

## The 3-minute pitch
| Time | Beat |
|---|---|
| 0:00–0:20 | **Problem:** one real person at one business, one painful task, how long it takes today. Use a real or clearly sourced number. |
| 0:20–0:35 | **The one-liner:** "<Name> is an agent that <does job> for <who>, and asks before it <risky step>." |
| 0:35–2:15 | **Live demo** of one flow: trigger → plan → tools → approval → result, with the trace visible. Keep the backup video ready, one click away. |
| 2:15–2:45 | **Beyond the prototype:** cost per run (from our real token count), how it plugs into tools the business already uses, data and GDPR, what we'd build next. |
| 2:45–3:00 | **Closing line** that calls back to the problem. |

**Name tip:** finalists pitch in **reverse alphabetical order** of the project name. A name starting late in the alphabet (S–Z) pitches early while the jury is fresh. A name starting with A goes last and gets the final word. Pick on purpose.

## Questions the jury will ask (have the answers ready)
1. Why is this an agent and not a workflow or Zapier? *(It decides which tool to use, handles the exceptions, and shows its reasoning.)*
2. What happens when the AI is wrong? *(The human approval step, confidence shown, the audit trail, it can be undone.)*
3. What does one run cost, and who pays? *(Use the real number from the Vertex usage.)*
4. What about data privacy and GDPR? *(Where data lives, no training on customer data, a European region.)*
5. What happens if someone puts instructions inside an email or document the agent reads (prompt injection)? *(Tool permissions, approval for actions.)*
6. Is there a real customer? *(Be honest: "not tested with real users yet". Name who we'd pilot with.)*

## Rules (from what we learned at earlier hackathons)
- **Show, don't claim.** Real output on screen, a live link, a QR code on the last slide.
- **Never invent** users, revenue, logos or testimonials. Label demo data as "demo data".
- **Commit every 30 minutes.** The 17:00 snapshot only sees what's pushed.
- **The submission is the first pitch.** The README opens with a GIF or screenshot, then the one-liner, then how to run it in 3 commands.
- Keep the Drive folder for the deck and video only, and don't touch it after 16:50 (the jury sees file timestamps).
