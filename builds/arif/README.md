# Jarvis for PoliPrep: Arif's build (Challenge A · Company Brain)

**Jarvis is PoliPrep's AI chief of staff. It speaks first, answers only from memory the team approved, and asks before it acts.** It reads PoliPrep's Gmail, Notion, Calendar, Canva, Instagram and Stripe (demo copies), writes each person a brief at 08:00, flags attacks, proposes drafts and meetings that wait for a tap, and **phones the CEO's real phone** when something is urgent.

![How Jarvis works](docs/jarvis-workflow.png)

**Run (Windows). Start it from `builds/arif` so the theme in `.streamlit/config.toml` loads:**
```powershell
cd builds\arif
python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```
Tests (offline, free): `.venv\Scripts\python -m pytest tests -q` (33 tests).

**Data:** real PoliPrep context (courses, prices, cohort rules, team roles) with **invented events**: every email, message, payment and number marked demo is made up. No real student, parent or client data. Files: `data_poliprep/`.

## The team (roles in code)
| Person | Role | Sees | Approves |
|---|---|---|---|
| Arif | CEO | everything | everything, and company-wide facts |
| Hamid | CFO | finance | finance facts, Stripe sync |
| Sara | CTO | tech | tech facts |
| Ulu | Social Media Strategist | marketing | marketing facts |
| Maria, Anna | Tutor | tutors | tutor facts |

## What it does
- **Speaks first:** an 08:00 brief per person (Slack-style chat, morning email mock-up, read aloud in an ElevenLabs voice) and alerts when an email arrives.
- **Phones the CEO:** an urgent email (Gemini says urgent AND code finds urgency words) makes Jarvis ring the CEO's real phone (an ElevenLabs voice agent over a Twilio number). It talks live and knows the team and the approved company facts (never finance-only facts: those don't go to the voice provider). It refuses to approve anything by voice. After the call, **"Collect drafts from the call"** turns what the CEO asked for (an email to students, a Zoom meeting) into drafts that wait for approval.
- **Curated memory:** facts proposed from sources wait for a person. Conflicts are flagged side by side ("€299 vs €399"), and the owner can **approve and replace, reject or edit**. Edits create versions, and the history is kept. **"Add what you know"** saves knowledge that isn't in any tool. An overview of the company and a **download** of the memory (Markdown or JSON, role-filtered) are on the Memory page.
- **Answers:** only from approved memory the asker may see, with sources. Every number must appear in the cited facts. Otherwise it says one of three things: **"I don't know"**, **"not available for your role, ask Hamid"**, or **"a note is waiting for review by …"**.
- **Only proposes:** replies, messages, announcements to students, Notion updates and Zoom meetings all wait in Approvals. The approver can **edit the draft**. A draft that relied on a fact that was replaced since is blocked until a person re-checks it.
- **Stripe → Notion:** the CFO or CEO syncs Stripe (demo export in Stripe's format, or a test-mode key). Jarvis computes revenue, flags the conflict with what Notion says, and proposes the Notion update.
- **Zoom:** Jarvis proposes meetings, for example "15 min with Anna to hand over the class". The meeting is created in Zoom only after approval (real with Zoom keys, a labelled demo link without).
- **Try to break it:** the sidebar's **Paste an email** delivers your own email, including attacks. The patterns catch common and disguised attacks (look-alike letters, invisible characters, CEO fraud), and Gemini catches reworded ones. A pasted email never rings a real phone.
- **Audit log:** every brief, question, citation, proposal, approval, call and export.

## Rules in code, not in the prompt
- The role filter runs before any model call; identity comes from the login picker, never from what is typed.
- Only approved memory is used. Approvals are checked by role: finance by the CFO, and company-wide facts by the CEO.
- Citations must be ids given to the model. Numbers must be in the cited facts.
- There is no send tool. Recipients are checked (colleagues, the original sender, known student groups, known Notion pages). Suspicious sources never lead to an action or a call. A stale draft needs review.
- One call per email. The voice agent has no tools, and approvals happen only in the app.

## Stack
Gemini 3.8 Flash on Vertex AI (location `global`, low thinking: a brief for 6 people in about 7 s, about $0.003 per brief) · ElevenLabs (voice and phone agent) · Twilio (phone line) · Streamlit · three.js (voice orb). Secrets live in `builds/arif/.env` (git-ignored); see `.env.example`.

## Honest limits
- Demo copies of the tools, not live connectors (except the phone call, and Zoom/Stripe when keys are set).
- Identity is a picker, not a login. Pattern checks catch the tested attacks and Gemini adds a second check; neither is a guarantee.
