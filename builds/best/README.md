# Jarvis, best-of-three build (Company Brain, Challenge A)

**On stage today:** a fictional scenario built on **Ariete Tech Solutions'** public services (AI agents and automations for professional firms, Turin). People, clients, events and numbers are invented; no Ariete data (`data_ariete/`, set with `JARVIS_DATA=data_ariete`). The same app also runs on **Filare Labs**, the team's shared fictional vineyard-sensor company (`data_filare/`, the default). Swapping company is a data swap.
Jarvis watches the team's email, chat, tasks and docs, keeps a shared memory that people curate, speaks first with a
morning brief and alerts, answers only from approved memory the asker may see, and **only proposes**: nothing is sent
until a person approves it.

This build starts from `builds/arif` (Jarvis: Streamlit + Gemini on Vertex AI, the most features), runs on the
shared Filare data, uses a **light theme**, and adds the best ideas from `builds/daddy` (Hamid) and `builds/uluhan` (Uluhan).

All data is synthetic. No real client or personal data.

## Run it

From `builds/best`, with Python 3.11+:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
set JARVIS_DATA=data_ariete
.venv\Scripts\python -m streamlit run app.py --server.port 8504
```

`JARVIS_DATA=data_ariete` is the stage demo; leave it out to run on Filare Labs (the default).

Open http://localhost:8504. With Google Application Default Credentials (or `GOOGLE_API_KEY`), Jarvis uses
`gemini-3.8-flash` on Vertex AI (location `global`); without them it runs a deterministic offline fallback.

Tests (offline, no network):

```
.venv\Scripts\python -m pytest tests -q
```

76 tests. New today: **Talk to Jarvis** (a live voice chat about your own brief in the browser; finance-only facts never go to the voice provider; it cannot approve anything), question chips, header counters and menu counts, and the demo dated to the hackathon day (Sat 21 Nov 2026).

## Settings (`.env`, git-ignored; see `.env.example`)

| Key | What it does |
|---|---|
| `JARVIS_DATA` | Which company to run on: a data folder in `builds/best` (default `data_filare`). Swapping company is a data swap. |
| `JARVIS_AUTO_DIAL` | `0` (default). Jarvis never rings a real phone by itself. The in-app call card always works. |
| `JARVIS_CALL_NAME` | Optional name Jarvis says on the phone. Default: the CEO's first name from the data. |
| `JARVIS_SWEEP_MINUTES` | Minutes between automatic morning sweeps while the app is open (default 30, `0` = off). |
| `ELEVENLABS_*`, `TWILIO_*`, `ZOOM_*`, `STRIPE_API_KEY` | Optional: voice, real phone call, real Zoom meetings, live Stripe (read-only test key). |

Runtime state is in `state/<data folder>/` (git-ignored). `demo_snapshot/<data folder>/` holds the 08:00 briefs Jarvis
wrote earlier with Gemini, so **Reset the demo** (CEO only) is instant.

## The data (`data_filare/`)

A copy of the repo-root `data/` (people, roles, emails, chat, tasks, docs, memory seed), extended with what the app needs:

- `company.json`: `approvers` (finance: CFO; tech: CTO or Field IoT engineer; sales: Sales lead; money facts always
  need the CFO; company-wide facts only the CEO), `overview`, `audiences` (winery customers), `stripe` (target page
  `doc-004`), and a `demo` block (default user, placeholders, the 7 jury checks).
- `demo_events.json`: the Langhe Viva confirmation email, the urgent frost email, and three paste-in examples
  (CEO fraud to Giulia, a reworded injection, a normal customer email).
- `stripe_charges.json`: invented winery subscription payments in Stripe's charge format (1 refund, 1 failed).
- `docs/revenue-tracker.md` and memory `mem-011`: the older revenue figure that the Stripe sync contradicts.
- `memory_seed.json` `mem-p03`: an old August budget estimate that conflicts with the approved budget and comes from an
  **older** source, so it can't replace it.

Optional sources (calendar, Canva, Instagram) are simply absent for Filare; the code skips missing files.

## What came from which build

| From | What |
|---|---|
| Arif (`builds/arif`) | The base: briefs and alerts, role filter in code, approved-only answers with citations, three kinds of "I don't know", number check, conflicts, edit and history, manual notes, export, paste-an-email attacks, urgent call with the orb and ElevenLabs voice, Zoom proposals, Stripe sync, stale drafts. |
| Uluhan (`builds/uluhan`) | An older source can't replace a newer approved fact (blocked "Approve and replace") and a **decision receipt** (active fact, rejected or replaced fact, who, when, which source, reason). Strict "not for your role" matching: only a clear, confident match says "ask X"; a tie or a weak match says plain "I don't know". |
| Hamid (`builds/daddy`) | **Reasons**: rejecting a fact or a draft needs a reason; approving a fact with a conflict or a number warning needs a written reason. **"How I got this"** under every answer. **Draft self-check** (one Gemini call lists statements the sources don't support; never blocks). **Quote check** on new memory (a fact without its exact words in the source is dropped). **Outbox privacy** (an approved item is visible only to people who may see every source it cites). **Timer** (the sweep runs by itself every 30 minutes). Approving a fact made from an email you pasted yourself is refused. |
| New here | Light theme, data-driven app (no company names in code), CEO-only reset, Gemini circuit breaker (2 failures in a row: offline for 60 s, shown in the status line), audit log filtered by role, value words stripped from the "not for your role" check, a re-sweep keeps alerts and escalation drafts. |

## Safety rules (in code, not in the prompt)

- Identity comes from the picker (standing in for company sign-in), never from what you type.
- The role filter runs before any model call. Restricted text never reaches the model, the answer, the trace, the export,
  the audit log or the outbox of someone who may not see it.
- Every source is wrapped as data; injection patterns (including disguised ones) are flagged and never acted on.
- Jarvis has no tool that sends. Only the person an action was proposed to can approve it; approvals go to a mock outbox.
- A suspicious or pasted email never rings a real phone. Finance-only facts never go to the voice provider.

See `CHECKS.md` for the jury walkthrough.
