# Token Mafia · Company Brain: the colleague who knows, speaks first, and asks before it acts

**GDG Torino AGENTHON 2026 · Track: Agentic AI for business · Challenge A (Company Brain)**
**Team:** Fakrul (Arif) Islam · Hamid Sajjadi · Uluhan Simsek

An AI colleague for a small company. It reads the team's email, chat, tasks and docs; tells each person what needs their attention **before they ask**; answers **only from memory that people approved**, with sources, or says **"I don't know"**; and **never acts without a person's approval**. The role filter, approvals, source ids and number check are enforced **in code, not in the prompt**, so a rival team can't talk them out; answer relevance and the phone agent's refusal still rely on the model's prompt.

![How Jarvis works: it reads, guards, a person approves, then it answers and proposes](pitch/agenthon-deck/assets/how-it-works.png)

> **No hosted demo: it runs locally (see below).** To see it without installing anything, watch the 21-second [film](pitch/jarvis-film/out/jarvis-film.mp4).

> **Start here: [Jarvis – your company brain](jarvis-your-company-brain/README.md)** (`jarvis-your-company-brain/`): the app we present. The judge's click sequence for the Ariete demo is in [`jarvis-your-company-brain/CHECKS.md`](jarvis-your-company-brain/CHECKS.md). Pitch deck: [`pitch/agenthon-deck/`](pitch/agenthon-deck/) · Film (21 seconds): [`pitch/jarvis-film/out/jarvis-film.mp4`](pitch/jarvis-film/out/).
>
> Demo company: a **fictional scenario built on Ariete Tech Solutions' public services. Not Ariete's data.** All people, clients, emails and numbers are invented.

## Run the stage demo (Ariete scenario)

**Set `JARVIS_DATA=data_ariete`.** If it is unset, the app runs on Filare Labs, our other fictional test company.

Windows PowerShell, from the repo root:
```powershell
cd jarvis-your-company-brain
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:JARVIS_DATA = "data_ariete"; $env:JARVIS_AUTO_DIAL = "0"
.venv\Scripts\python -m streamlit run app.py --server.port 8504
```

macOS / Linux:
```bash
cd jarvis-your-company-brain
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
JARVIS_DATA=data_ariete JARVIS_AUTO_DIAL=0 .venv/bin/python -m streamlit run app.py --server.port 8504
```

Open http://localhost:8504 and follow the **Ariete click sequence** in [`CHECKS.md`](jarvis-your-company-brain/CHECKS.md). Tests (offline; they run on the Filare data): `.venv/bin/python -m pytest tests -q` (Windows: `.venv\Scripts\python -m pytest tests -q`) from `jarvis-your-company-brain/` (87 passing). On 21 Nov at 16:18 we also ran a clean start of the Ariete demo in the Streamlit UI on Gemini: the morning brief loaded with sources, and the Wi-Fi password question got "I don't know".

## How we built it: three builds in parallel, then the best ideas merged
Each of us built a full version of Challenge A in the morning. Our own red-team agents (jury scorer, devil's advocate, failure hunter) attacked all three, and all three passed the 7 jury checks. We then merged the best ideas into one app, **Jarvis**:

- **Arif:** the base. Briefs and alerts nobody asked for, the role filter in code, approved-only answers with citations, conflicts with edit and history, an urgent call to the CEO (in-app call card; a real phone call through ElevenLabs + Twilio only when configured and opted in), Zoom proposals and payment approval requests, Stripe sync (off in the Ariete demo), paste-an-email attacks.
- **Hamid:** reasons for rejecting or approving despite a warning, "How I got this" under every answer, the exact-quote check on new memory, the draft self-check, outbox privacy, the 30-minute sweep timer.
- **Uluhan:** change control for company facts (an older source can't replace a newer decision, with a decision receipt), strict "not for your role" matching, the circuit breaker when Gemini fails.

The three original solo builds are in the Git history of this repo; only `jarvis-your-company-brain/` is in the current tree.

## The 7 jury checks, and how each one is enforced
| # | Check | How Jarvis enforces it |
|---|---|---|
| 1 | It speaks first | A sweep writes each person's 08:00 brief and alerts nobody asked for (every 30 min while the app runs). For an urgent email it alerts the CEO with an in-app call card. A real phone call happens only when phone keys are set, Gemini mode is on and auto-dial is switched on (`JARVIS_AUTO_DIAL=1`) |
| 2 | People curate the memory | Facts wait as "pending"; only approved facts are ever used; conflicts are shown side by side |
| 3 | It knows who's asking | The role filter runs in code **before** the model sees anything. The finance group and the CEO can read a finance fact; others are refused. Typing "I'm the CFO" changes nothing |
| 4 | It cites | Only ids given to the model count as citations; answers show their sources |
| 5 | It admits gaps | No approved, visible, cited fact → "I don't know" |
| 6 | It only proposes | No send tool exists. Drafts wait for the named person's approval; an approved message goes to a mock outbox |
| 7 | It fits the team's day | A workspace with channels, each person's morning email, the brief read aloud, and Talk to Jarvis (a live voice chat about your own brief) |

## Try to break it
Prompt-injection emails, CEO-fraud payment requests, disguised characters, reworded attacks (caught by a second Gemini check), "I'm the CFO" tricks, approving someone else's draft, and stale drafts after a fact changed are all blocked and covered by tests.

## Honest limits
- Demo data, not live connectors. The phone call and Zoom are real only when keys are set and rehearsed; by default the call is an in-app card and approved messages go to a mock outbox. Stripe is not connected in the Ariete dataset.
- Identity is a picker standing in for company sign-in, not a company login.
- We make no voice-privacy promise: the "Play my brief" text can include finance items from the listener's own brief. On stage we show the CEO brief on screen.
- Date precision is not verified: offline Jarvis answered a question about a 2032 Bellini invoice with the 2026 invoice. This is on our red-team list.
- Pattern and AI checks catch the attacks we tested; neither is a guarantee.
- No API keys in this repo: the app reads a git-ignored `.env` (see `jarvis-your-company-brain/.env.example`).

## Docs
[Event brief](docs/hackathon-brief.md) · [Challenge A plan](docs/PLAN-A.md) · [Our strategy](docs/STRATEGY.md) · [Red-team report](docs/red-team-compare.md)
