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

## Track brief (paste at 10:00)
> _Sealed until kick-off. Paste the full text here, word for word._
