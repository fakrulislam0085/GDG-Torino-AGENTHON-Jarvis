# GDG Torino AGENTHON: event brief

Source: the event portal (agenthon-portal.gdgtorino.it), read on Sat 21 Nov 2026 at 09:40. Update the track brief section at 10:00.

## Team
- Portal team name: **Team Islam** (our team is Token Mafia; check which name the jury should see)
- Fakrul Islam, Hamid Sajjadi, Uluhan Simsek
- Track 1: **Agentic AI for business**. Room: **The Stage**, floor −1 (south of reception). The keynote is in the same room.

## Today's schedule
| Time | What |
|---|---|
| 09:00 | Doors open, coffee |
| 10:00 | Kick-off and track briefs. **The brief is unsealed on the portal** |
| 10:15 | Build time |
| 13:00 | Lunch |
| 14:00 | Build time |
| **17:00** | **Submissions close (hard deadline)** |
| 17:15 | Finalists pitch to the jury |
| 18:30 | Awards |
| 19:00 | Pizza and beer |

## Deliverables (Submit tab)
- **Project name.** Finalists pitch in *reverse alphabetical order* of this name.
- **Short description.** What it does and who it's for, 1000 characters max.
- **GitHub repository.** The code built today, in a **public** repo.
- **Google Drive folder.** Optional. The deck and any other materials, shared as "Anyone with the link can view".
- **Notes.** Optional, for the jury.
- At 17:00 they record the repo's **latest commit** and the **last-modified time of each file** in the Drive folder. Anything changed after that doesn't count.
- Check that every link opens from another account before saving.

## Judging
Each track has a jury of 5: 1 from the track sponsor, 1 from GDG Torino, 3 external.

| Criterion | Where we prove it |
|---|---|
| Innovation | The insight slide, plus the moment in the demo that a plain chatbot can't do |
| Fit with the track theme (agentic AI for business) | The agent takes real actions with tools for a named business user, not just chat |
| Feasibility beyond the prototype | Cost per run, who pays, how it plugs into tools the business already uses, data and GDPR, human approval |
| Quality of the technical execution | A live demo end to end, the agent trace and tool calls on screen, a clean repo and README |
| Quality of the pitch | 3 minutes: problem → solution → **live demo** → feasibility → closing line |

- The pitch is about **3 minutes** in our track, with questions after. "A demo that works beats ten slides."
- **Only 8 to 12 teams per track pitch.** The jury picks finalists from the *submissions*, so the README, the description and the demo video must win without us in the room.
- Prizes: Amazon gift cards for the top 2 per track, split among the team. Books for standout projects.
- **Special prize: Best use of ElevenLabs.**

## Our Google Cloud setup (done 10:20)
- The credits were claimed on Fakrul's personal Gmail. **They expire Sat 21 Nov at 22:36.**
- Billing account: `GDP Event Credit: DevFest Alps 2026`. It holds the credits only, with no card. **Don't click "Start free trial".**
- Project: **`token-mafia-agenthon`** (number 757133682196), linked to that billing account.
- The Vertex AI API (now called "Agent Platform API", `aiplatform.googleapis.com`) is enabled.
- `gemini-3.8-flash` is served only from location **`global`** (404 in europe-west1, europe-west4, us-central1). Use `GOOGLE_CLOUD_LOCATION=global`.
- Endpoint: `https://europe-west1-aiplatform.googleapis.com/v1/projects/token-mafia-agenthon/locations/europe-west1/publishers/google/models/gemini-3.8-flash:generateContent`
- Studio's default model is "Gemini 4 Carbon" in the `global` region. Pick `gemini-3.8-flash` instead: the portal only confirms GA models are covered.

## Resources
- **Google Cloud: $30 of credits, valid for 12 hours.** Claim them at g.dev/credits/devfest-alps-2026 *just before building*, with a personal Gmail.
  - Use **Gemini through Vertex AI**, not AI Studio (AI Studio stays on the free tier and doesn't use the credits).
  - GA models are fine: `gemini-3.8-flash` ($0.75 per million tokens in, $3.75 out), `gemini-3.5-flash`, `gemini-3.1-flash-lite`.
  - **Don't use the europe-west12 region (Turin)**: it is excluded.
  - Covered: Cloud Run, Cloud Functions, Firebase on the Blaze plan, Firestore, Cloud SQL, BigQuery, Maps, Speech-to-Text and Text-to-Speech.
  - Not covered: GKE, partner models (Claude, Llama), preview models, and probably Veo Lite.
  - Images and video: Nano Banana allows about 1 image a minute. Veo 3.1 Fast costs $0.10 a second. Draft on 4-second clips.
- **ElevenLabs:** a free Creator plan coupon from the bot in the #coupon-codes channel on the ElevenLabs Discord (event "AGENTHON: Waiting for DevFest Alps"). Use the API for voice so the credits last.
- **HyperFrames** for an AI-made demo video: `npx hyperframes skills update`.
- Wi-Fi: Feat. House Guest / `#venturingtogether`

## Track brief (revealed at 10:28, word for word)

**Agentic AI in companies.** Track sponsor: Ariete Tech Solutions.

**The challenge: build an AI your team would trust.**
Build an AI that works in the background and asks before it acts, then defend it live against a jury and **rival teams trying to break it**.
Flashy demos don't win here. The winner is the build that is right, admits what it doesn't know, and never acts without a person's approval.

Pick one of two challenges (one track, one jury, one ranking).

### Challenge A · Company Brain: "the colleague who knows, and speaks first"
One tool that watches a team's work (email, chat, tasks, docs), keeps a shared memory that people curate, and tells each person what needs their attention before they ask. A chatbot over documents doesn't count.
**Seven checks; the jury marks each one yes or no:**
1. **It speaks first.** Show a brief or alert it made on its own, without anyone asking.
2. **People curate the memory.** Approve one memory item and reject one, live. Then ask a question that only the approved item can answer.
3. **It knows who's asking.** Ask the same question as a finance person and as a tech person. One gets the answer, the other doesn't.
4. **It cites.** Every answer shows where it came from.
5. **It admits gaps.** Ask something that isn't in the data, and it says "I don't know".
6. **It only proposes.** Show an action waiting for approval. Nothing happens until a person approves it.
7. **It fits the team's day.** Show where the team would meet it: a chat window, a morning email, a Slack-style mock-up. No real connection needed.

### Challenge B · Back Office Autopilot: "the colleague who does, and asks first"
Pick one back-office process and run it end to end: invoices, payments, reminders, payroll inputs or expense reports. The rules are known, but every case has exceptions. The autopilot runs the whole process, stops at the exceptions, and asks a person before anything that can't be undone.
**It must:**
- **Run end to end, with a person in the right places.** Raw input in, finished output out. It stops at exceptions and waits for approval before anything is sent, paid or exported.
- **Solve an urgent business problem.** Show who loses time or money today, how much, and what the autopilot saves.
- **Leave a trail.** Show the log of what it did, on which input, and who approved it.

### Data
- If you know the industry's real data formats, make your own synthetic data. If you don't, start from an open-source dataset.
- **No real client or personal data.**
