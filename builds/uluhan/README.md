# Company Brain · Uluhan's Challenge A build

Run from the repository root with Python 3.12 and `uv`.

```bash
uv run --no-project --python 3.12 --with-requirements builds/uluhan/requirements.txt uvicorn --app-dir builds/uluhan brain.server:app --port 8010
```

## Signature moment: change control for company facts

1. Start from the approved Q1 2027 cloud-budget fact: **EUR 18,000**.
2. Simulate **Archived cloud budget email**; it claims the budget is **€12,000**.
3. Show the Decision Receipt with the approved fact and incoming claim side by side.
4. Explain why it was blocked: the email is older evidence, and only **Giulia/CFO, Marco/CTO, or Elena/CEO** may change this fact.
5. Reject the archived claim.
6. Ask **What is the Q1 2027 cloud budget?** The answer remains **€18,000**, with its citation.

> “Most AI assistants believe the last thing they read. Ours treats an incoming email as a claim, not a decision. When a message contradicts an approved company fact, it shows both side by side, says why it didn't change anything, and only the person with authority can update the record. Your company's knowledge changes by decision, not by inbox.”

**Limits:** Identity is chosen in a demo picker (no authentication).

Open [http://localhost:8010](http://localhost:8010). This build reads the team's shared synthetic **Filare Labs** data from the repository's [data directory](../../data). [CHECKS.md](CHECKS.md) gives the exact seven-check route.

**Change control for company facts.** The Company Brain watches new information and tells the team what needs their attention. Incoming claims go to review. An archived estimate cannot replace a newer approved decision, and a draft stays in Approvals until its designated reviewer acts. Answers use only approved evidence the selected person can see.

## Three-minute walkthrough

| Time | Show |
|---|---|
| 0:00–0:35 | Start as **Luca** and run the 08:30 sweep. His DM alerts him to the €14,640 second notice. Point to the pending review draft and empty Outbox. Approve it as Luca and show the one mock outbox entry. |
| 0:35–1:15 | Switch to **Sara**. Ask **When does the Langhe fix roll out?** Approve `mem-p01` and reject `mem-p02` in Memory review. Ask again and open `chat-003`. The first answer abstains. The second gives Thursday 26 November at 07:00. |
| 1:15–1:55 | Ask **What is our cash runway?** as Giulia and Sara. Open Giulia's `email-003` citation. Sara receives an abstention with no restricted fact or citation. Ask Giulia **What is our Q2 2027 cloud budget?** for the separate real gap. |
| 1:55–2:40 | As Sara, replay **Archived cloud budget email** in **Simulate incoming email**. Open incoming `email-006`, then ask **What is the Q1 2027 cloud budget?** Open `email-005`. The archive says €12,000, and the approved budget remains €18,000. The review card explains why promotion is blocked. |
| 2:40–3:00 | Close with one landing point for a pilot. Read one existing inbox and task queue, put decisions in front of their owners, and measure time to resolve conflicts and how often outdated figures reach downstream work. |

Backup jury probe as **Sara**. Trigger **Suspicious email to Sara**. The agent flags `email-008`, creates no memory or action from it, and excludes that sender from draft recipients.

## Vertex and offline mode

With no credentials, the default is **Offline fallback**. To force that mode, prefix the run command with `BRAIN_MODE=offline`. For the team's Vertex project, configure ADC through an account that already has access, then start the app with these environment variables.

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=token-mafia-agenthon
export GOOGLE_CLOUD_LOCATION=eu
export GEMINI_MODEL=gemini-3.8-flash
```

The build also accepts a Vertex AI key via `GOOGLE_API_KEY` with `GOOGLE_GENAI_USE_VERTEXAI=true` and no `GOOGLE_CLOUD_PROJECT`. Keep credentials out of Git. The upstream build verified Gemini on the `eu` endpoint. For the shared-data version, run the following against the configured server to check the current flow, model modes and token usage.

```bash
uv run --no-project --python 3.12 --with-requirements builds/uluhan/requirements.txt builds/uluhan/live_checks.py http://127.0.0.1:8010
```

Copy `.env.example` to `.env` inside this build to configure keys locally. With `ELEVENLABS_API_KEY`, the **Play voice brief** button reads the selected person's brief.

## Tests

```bash
cd builds/uluhan
BRAIN_MODE=offline uv run --no-project --python 3.12 --with-requirements requirements.txt python -m pytest -q
```

Tests cover the shared-data jury sequence, role boundaries, unsupported questions, evidence replay and approval. The legacy synthetic seed remains for regression tests. The running app loads only the repository's shared company.

The persona picker simulates identities. The demo has no production sign-in, live connectors, or persistent storage. The 08:30 button simulates an external scheduler tick. Approving a draft writes only to the local mock outbox.
