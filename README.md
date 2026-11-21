# Token Mafia · Company Brain: the colleague who knows, speaks first, and asks before it acts

**GDG Torino AGENTHON 2026 · Track: Agentic AI for business · Challenge A (Company Brain)**
**Team:** Fakrul (Arif) Islam · Hamid Sajjadi · Uluhan Simsek

An AI colleague for a small company. It reads the team's email, chat, tasks and docs; tells each person what needs their attention **before they ask**; answers **only from memory that people approved**, with sources, or says **"I don't know"**; and **never acts without a person's approval**. Every safety rule lives in **code, not in the prompt**, so a rival team can't talk it out of them.

![How Jarvis works: it reads, guards, a person approves, then it answers and proposes](pitch/agenthon-deck/assets/how-it-works.png)

> **Start here: [`builds/best`](builds/best/README.md)** is the build we present: the best ideas of all three builds, on a fictional scenario built on Ariete Tech Solutions' public services. Pitch deck: [`pitch/agenthon-deck/Jarvis AGENTHON A.pdf`](pitch/agenthon-deck/). Film: [`pitch/jarvis-film/out/jarvis-film.mp4`](pitch/jarvis-film/out/). Every build below stays in the repo.

## How we built it: three builds in parallel, then the best ideas merged
Each of us built a full version of Challenge A until 13:00. Our own red-team agents (jury scorer, devil's advocate, failure hunter) then attacked all three. **All three pass the 7 jury checks.** We moved the best ideas between builds.

| Build | Built by | Stack | What it is best at | Run and details |
|---|---|---|---|---|
| `builds/arif` · **Jarvis for PoliPrep** | Arif | Streamlit, Gemini on Vertex AI, ElevenLabs, Twilio | **Phones the CEO's real phone** for urgent emails and talks live; voice brief with a reactive orb; conflicts + edit + history; Stripe → Notion; Zoom proposals; paste-an-email attacks | [README](builds/arif/README.md) · [CHECKS](builds/arif/CHECKS.md) |
| `builds/daddy` · **Filare Brain** | Hamid | Python standard library, Gemini over HTTPS | Zero dependencies; numbers in answers must match the facts; approvers edit drafts; HTTP and CSRF guards; "not for your role" vs "not approved yet" | [README](builds/daddy/README.md) · [CHECKS](builds/daddy/CHECKS.md) |
| `builds/uluhan` · **Company Brain** | Uluhan | FastAPI, Gemini on Vertex AI | Change control for company facts: an older source can't replace a newer decision; decision receipts; billing pilot plan | [README](builds/uluhan/README.md) · [CHECKS](builds/uluhan/CHECKS.md) |
| `builds/best` · **Jarvis, best of three** *(presented)* | the team | Streamlit (light UI), Gemini on Vertex AI, ElevenLabs, Twilio | Arif's Jarvis + Hamid's quote check, draft self-check, outbox privacy, timer + Uluhan's change control and strict role matching; Talk to Jarvis; Ariete scenario or Filare data | [README](builds/best/README.md) · [CHECKS](builds/best/CHECKS.md) |
| `builds/mafia` · **the mix** | Hamid, Uluhan | Python standard library, Gemini over HTTPS | Hamid's engine + Uluhan's workspace UI and agent trace + Arif's escalation call; frost-date hold for the customer reply | [README](builds/mafia/README.md) · cold-open film: [`pitch/cold-open/out/`](pitch/cold-open/out/) |

Shared demo company for Hamid's, Uluhan's and the best build: **Filare Labs** (fictional vineyard-sensor startup), in [`data/`](data/). Arif's build also has a PoliPrep dataset: real course facts with invented events.

## The 7 jury checks, and how each one is enforced
| # | Check | How (in every build) |
|---|---|---|
| 1 | It speaks first | A scheduled sweep writes each person's brief and alerts nobody asked for (Arif's build also phones the CEO) |
| 2 | People curate the memory | Facts wait as "pending"; only approved facts are ever used; conflicts are shown side by side |
| 3 | It knows who's asking | The role filter runs in code **before** the model sees anything; typing "I'm the CFO" changes nothing |
| 4 | It cites | Only ids given to the model count as citations; answers show their sources |
| 5 | It admits gaps | No approved, visible, cited fact → "I don't know" |
| 6 | It only proposes | No send tool exists; drafts wait for the named person's approval |
| 7 | It fits the team's day | Slack-style workspace, morning email, voice brief |

## Try to break it
Prompt-injection emails, CEO-fraud payment requests, disguised characters, reworded attacks (caught by a second Gemini check), "I'm the CFO" tricks, approving someone else's draft, and stale drafts after a fact changed are all blocked and covered by tests in each build.

## Honest limits
- Demo data, not live connectors (Arif's build makes real phone calls, and real Zoom/Stripe calls when keys are set).
- Identity is a picker, not a company login.
- Pattern and AI checks catch the attacks we tested; neither is a guarantee.
- No API keys in this repo: each build reads its own git-ignored `.env`.

## Docs
[Event brief](docs/hackathon-brief.md) · [Challenge A plan](docs/PLAN-A.md) · [Our strategy](docs/STRATEGY.md)
