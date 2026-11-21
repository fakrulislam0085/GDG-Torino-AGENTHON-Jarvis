# Brain for Filare Labs: Arif's build (Challenge A · Company Brain)

**Run (Windows, from the repo root):**
```powershell
python -m venv builds\arif\.venv; builds\arif\.venv\Scripts\python -m pip install -r builds\arif\requirements.txt
builds\arif\.venv\Scripts\python -m streamlit run builds\arif\app.py
```
On macOS or Linux, use `builds/arif/.venv/bin/python`. Tests (offline, free): `builds\arif\.venv\Scripts\python -m pytest builds\arif\tests -q`

**A colleague that speaks first, answers only from memory the team approved, and asks before it acts.** Brain watches Filare Labs' email, chat, tasks and docs (shared fake data in `../../data/`). At 08:00 it posts each person a brief nobody asked for, flags attacks hidden in emails, proposes actions that wait for a click, and says "I don't know" when the approved memory doesn't say.

**Demo data only.** Filare Labs and everyone in it are fictional.

## Gemini (Vertex AI, event credits)
Put this in `builds/arif/.env` (git-ignored), or log in with `gcloud auth application-default login`:
```
GOOGLE_CLOUD_PROJECT=token-mafia-agenthon
GOOGLE_CLOUD_LOCATION=europe-west1
GEMINI_MODEL=gemini-3.8-flash
# or a Vertex AI API key: GOOGLE_API_KEY=...
# optional voice brief: ELEVENLABS_API_KEY=...  ELEVENLABS_VOICE_ID=...
```
With no credentials it runs an **offline fallback** (deterministic keyword matching and templates), and the sidebar badge says so. Every safety rule below holds in both modes.

## Design: rules in code, not in the prompt
- **Answers come only from approved memory** the asker may see (`brain/memory.py`, `brain/answer.py`). Raw emails are never searched directly.
- **The role filter runs before any model call** (`brain/access.py`). Identity comes from the role picker, never from the question text.
- **Citations are checked in code.** Only ids we gave the model count. No valid citation means "I don't know".
- **Brain has no tool that sends.** `propose.approve_action()` is called only by the Approve button, and only the person the action was proposed to can approve it. Recipients are limited in code to colleagues, or the original sender of a normal email.
- **Injection defence** (`brain/guard.py`): suspicious emails are flagged in the brief, never shown to the model as instructions, and can never lead to an action.
- **New memory inherits the source's access list** by code (`memory.add_pending`), not by the model.
- **Audit log** of every brief, question, citation, proposal and approval (`state/audit.jsonl`, and the Audit log page).

## Pages
- 🧠 **Brain:** a Slack-style workspace. Brain's DM shows the 08:00 brief and alerts with 📎 sources, plus Ask Brain. The channels show the team's chat.
- 🗂️ **Memory review:** approve or reject what Brain proposed to remember.
- ✅ **Approvals:** proposed messages and replies, with Approve / Reject, and the outbox (mock).
- 📧 **Morning email:** the same brief as an email mock-up.
- 📜 **Audit log:** everything Brain did, plus Gemini token use for the cost-per-brief number.
- **Sidebar:** role picker, 08:00 sweep, *Simulate: a new email arrives*, Reset demo, and the **Jury checklist**. It sets up each of the 7 checks and turns ✅ when it has been shown.

## Honest limits
- Fake data, no real connectors (Gmail, Slack and Drive would replace the JSON files).
- The offline fallback matches by keywords, so it is less clever than Gemini, but it is just as safe.
- The injection detector is pattern-based: it catches the tested attacks, and isn't a guarantee.
