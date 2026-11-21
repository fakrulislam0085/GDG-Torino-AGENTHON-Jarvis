# Filare Brain: Hamid's build (Challenge A, Company Brain)

**Run (from the repo root, Python 3.10+, nothing to install):**

```bash
python builds/daddy/app.py
```

Open http://localhost:8020. Pick who you are on the left. Demo links work too: `http://localhost:8020/?as=sara&view=approvals`.

**Tests:** `python -m unittest discover -s builds/daddy/tests -v` (15 tests: the 7 checks + red-team attacks + a fake model that misbehaves on purpose).

## What it is

A colleague for a small company (Filare Labs, the shared synthetic data in `data/`). It reads the team's email, chat, tasks and docs, and:

- **speaks first**: a morning brief for each person, posted on its own, plus an alert when an important email arrives;
- **knows only what people approved**: answers come only from memory a person approved, filtered by role, with a citation on every line;
- **says "I don't know"** when the approved memory doesn't answer, and tells you when the answer exists but isn't for your role, or is waiting for a person's review;
- **never acts on its own**: it drafts emails and task changes, and each one waits for the one person named on it. That person can edit the draft, approve it or reject it with a reason. Everything goes in the audit log.

## Human in the loop: where a person decides

| What the Brain wants to do | Who decides | What happens before they decide |
|---|---|---|
| Add a fact to memory (e.g. "fix rolls out Thursday") | Anyone who can see all its sources | Nothing. The fact is never used in answers |
| Send an email (e.g. reply to the customer, confirm an invoice) | The named approver, e.g. Paolo or Luca | Nothing is sent. The approver can edit the draft first |
| Unblock or create a task (e.g. certificate renewal) | The named approver, e.g. Marco | The task stays blocked. Sara sees "waiting for Marco" |
| React to a suspicious email | Nobody: it is never turned into memory or an action | People are warned and told to verify by phone |

## How it works

```
data/ (email, chat, tasks, docs) ──► role filter (code) ──► Gemini or plain rules ──► guards (code) ──► a person decides ──► audit log
```

| File | What it does |
|---|---|
| `brain.py` | Everything that keeps people in control: role filter, approved-only memory, citation and number checks, proposal checks, approvals, audit log |
| `llm.py` | Gemini 3.8 Flash on Vertex AI (eu multi-region, low thinking) over plain HTTPS (no SDK). Returns `None` on any error, so the Brain falls back to rules |
| `app.py` | Standard-library web server + the morning sweep on a timer (it runs on its own at start-up) |
| `web/index.html` | Slack-style workspace: Brain DM, morning email, Approvals, Memory review, channels, email, audit log, outbox, jury checklist |
| `demo_extra.json` | Two emails you can make arrive live (a customer's frost warning, a fake CEO payment request) and the offline fallback results |

**Where the model is used:** reading a new email (alert, memory candidates with an exact quote, one proposal, suspicious or not), proposing actions in the morning sweep, the brief's opening line, phrasing answers. **Where it is not:** deciding who sees what, which memory counts, whether a citation is real, whether anything happens.

**Guards in code, whatever the model says:**
- The role filter runs before the model is called. Finance memory never reaches the prompt for a tech person, so "I'm the CFO" in the message does nothing.
- Citations must be ids we gave the model; otherwise the answer becomes "I don't know".
- Every number in an answer must appear in the cited facts; otherwise the facts are shown verbatim.
- A memory candidate must quote the email word for word, or it is dropped.
- A proposal is blocked if its sources are suspicious, if the approver can't see them, if an internal recipient can't see them (no leaks), or if an external recipient isn't the sender of a cited email (no exfiltration).
- Only the named approver can approve (HTTP 403 for anyone else). There is no "send" tool for the model at all.
- The `_demo` hints in the shared data are stripped before anything reaches the model or the screen.

## Turn on Gemini (Vertex AI, event credits)

Put one of these in a `.env` next to `app.py` or at the repo root (both are git-ignored), or export them:

```bash
GOOGLE_API_KEY=...                    # a Vertex AI API key, or:
GOOGLE_ACCESS_TOKEN=...               # output of: gcloud auth print-access-token
# or run `gcloud auth application-default login` once; the app finds the credentials file itself
GOOGLE_CLOUD_PROJECT=token-mafia-agenthon   # default
GOOGLE_CLOUD_LOCATION=eu                    # default; gemini-3.8-flash is NOT in europe-west1 (404). "global" also works
GEMINI_THINKING=low                         # default; much faster for these short JSON tasks
GEMINI_MODEL=gemini-3.8-flash               # default
BRAIN_MODE=offline                          # force the rules-only mode
SWEEP_EVERY_MIN=30                          # how often the sweep runs on its own
```

The sidebar says which mode is on. If a Gemini call fails, that step falls back to rules and the trace says so. The audit log shows calls, tokens and cost so far.

**Cost (estimate, from the event prices: $0.75 per M tokens in, $3.75 per M out):** a morning sweep for 7 people is 14 calls of about 1 to 4k tokens, roughly $0.03, so about half a cent per person per day. An answer is about 1k tokens, under $0.001.

## Limits

- Synthetic data only, kept in memory. **Reset demo** restores it.
- The outbox is a mock: nothing is ever sent.
- Identity comes from the "You are" picker. A real deployment would use the company login (Google Workspace / Microsoft SSO).
- Offline, answers use keyword matching, which is strict: it says "I don't know" rather than guess. With Gemini, phrasing is freer and the same guards apply.
- Offline, the morning proposals and the reading of the two live emails come from `demo_extra.json`, labelled "offline" on screen.
- Not tested yet with live Gemini on this machine (no credentials here). The fake-model tests cover how the guards handle a bad model.
- Next steps: real connectors (Gmail, Slack, Drive), embeddings for retrieval, approvals inside Slack.
