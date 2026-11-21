# Company Brain: Uluhan's build (Challenge A)

**The colleague who knows, speaks first, and never acts without you.** A Gemini agent watches a small team's email, chat, tasks and docs. At 08:00 it writes each person a brief nobody asked for. It answers only from memory that people approved, cites every answer, says "I don't know" when it doesn't know, and drafts actions that wait for a person's approval.

**Demo data only.** Officina Lume, Verdi Logistics, NordPrint and every person here are fictional.

## Run it

From the repo root:

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r builds/uluhan/requirements.txt
cd builds/uluhan && ../../.venv/bin/python -m uvicorn brain.server:app --port 8010
```

Open http://localhost:8010. With no Gemini credentials it runs the **offline fallback**, and the header badge says so.

### Turn on Gemini (Vertex AI, event credits)

Use one of these:

```bash
# A: Google Cloud user credentials with access to the team project
export GOOGLE_CLOUD_PROJECT=token-mafia-agenthon GOOGLE_CLOUD_LOCATION=europe-west1
gcloud auth application-default login

# B: a Vertex AI API key
export GOOGLE_API_KEY=... GOOGLE_GENAI_USE_VERTEXAI=true
```

`GEMINI_MODEL` defaults to `gemini-3.8-flash`. `BRAIN_MODE=offline` forces the fallback. Never commit keys.

## The seven checks, and where they're enforced

| # | Check | What you click | What enforces it |
|---|---|---|---|
| 1 | Speaks first | **Run 08:00 sweep** → each person gets a DM brief; a new email raises an alert | `agents.sweep`, `brief`, `ingest` |
| 2 | People curate memory | **Memory review** → approve M8, reject M9 → ask *"Where should we send the Atlas milestone 2 invoice?"* | Retrieval only returns `approved` items (`tools._memory_hits`) |
| 3 | Knows who's asking | Ask *"How much is Atlas milestone 2?"* as Giulia (finance), then as Marco (tech) | Role filter runs **before** the model sees data; restricted items show only id + topic |
| 4 | Cites | Every answer and brief item has 📎 chips that open the source | `answer` / `submit_brief` drop any citation the person can't see or that isn't approved |
| 5 | Admits gaps | *"What is the budget for the Atlas mobile app?"* | An answer without a valid citation is downgraded to "I don't know" in code |
| 6 | Only proposes | Drafted emails sit in **Approvals**; the outbox stays empty until the owner approves | No agent has a send tool. Approval is an HTTP call by a person; the wrong role gets 403 |
| 7 | Fits the day | A Slack-style workspace with the brief as a morning DM | `web/index.html` |

**Extras for the red team**
- **Stale memory.** *Simulate incoming email → NordPrint new terms*. The brain does not overwrite "30 days". It raises a conflict to Finance and drafts a reply asking for the signed amendment.
- **Prompt injection.** *Simulate incoming email → Suspicious email*. The email is flagged and nothing is approved or sent. If the model misses it, a code backstop flags it anyway.
- **Replay.** Sending the same email twice changes nothing.
- **Trace.** The right-hand panel shows every tool call, every refused action (red `!`), tokens and cost per run.

## Architecture

```
trigger (08:00 sweep · new email · question)
   └─ agent (Gemini function calling, forced tool use, max 10 turns)
        └─ tools.py  ← permission checks, quote verification, recipient allowlist, citation validation
             └─ store.py (in-memory demo company, audit log)
   └─ if Gemini fails or is missing: deterministic planner, same tools, labelled "offline" in the trace
```

Three agents with separate toolsets. **ingest** reads one new source and proposes memory candidates. **brief** writes a person's morning brief and drafts emails. **ask** answers one question. None of them can approve memory or send anything.

## Tests

```bash
cd builds/uluhan && ../../.venv/bin/python -m pytest -q
```

There are 25 tests: one or more per jury check, plus the red-team cases. A scripted fake Gemini checks that the guards hold even when the model misbehaves.

## Limits

- The demo company is synthetic and stored in memory. **Reset** restores it.
- The outbox is a mock: nothing is ever sent.
- Retrieval is keyword-based over about 10 memory items. A real deployment needs embeddings and real connectors (Gmail, Slack, Drive).
- The offline fallback uses fixed extraction results for the demo emails. The trace labels those runs "offline".
