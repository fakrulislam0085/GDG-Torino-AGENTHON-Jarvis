# Hard questions: Jarvis (AGENTHON)
| # | Question they will ask | Short answer (facts) | Fact IDs |
|---|---|---|---|
| 1 | Two sources disagree. Who wins? | Neither, automatically. For example, two prices for the same plan: Jarvis shows both side by side, and the owner decides: replace, reject or edit. The old version stays in history. | F05, F12 |
| 2 | What stops a confident but wrong answer with a real-looking source? | Only ids we gave the model count as citations, and every number must appear in the cited facts. Otherwise we show the approved fact word for word, or say "I don't know". | F05 |
| 3 | Can someone talk it into showing finance data? | No. The role filter runs in code before the model sees anything, so finance facts never reach a tech person's prompt. Typing "I'm the CFO" changes nothing. | F05, F13 |
| 4 | Can the agent send an email or approve something by itself? | No. There is no send tool. Drafts wait for the named person's tap. On the phone it refuses "approve it". | F05, F10 |
| 5 | What about prompt injection or fraud emails? | Patterns catch the common and disguised ones, and a second Gemini check caught a reworded attack the patterns missed. Suspicious emails never create memory, actions or calls. | F08, F09 |
| 6 | Is this really agentic, or chat over documents? | It runs on its own: it briefs at 08:00, reads new email, flags an urgent one and phones the CEO, and drafts actions and Zoom meetings. Each step is logged. | F03, F10, F12 |
| 7 | What does it cost? | About $0.003 per morning brief on Gemini 3.8 Flash, measured today. The cost of a phone call isn't measured yet. | F11 |
| 8 | What if Gemini or the Wi-Fi fails on stage? | If Gemini fails, the safety rules still run in code, so nothing gets out, and the screen shows it is offline. I'll show you. | F05 |
| 9 | GDPR? Where does the data go? | Demo data only today. The AI runs on Google Vertex AI. Finance facts never go to the voice provider. A real deployment needs a data processing agreement (DPA) and a company login. | F13 |
| 10 | Who would pay, and how big is the market? | Small firms with scattered knowledge, starting with Ariete's clients through a pilot. We haven't sized the market yet. | F14 |
| 11 | Is it production-ready? | No. Identity is a picker, the connectors are demo copies (except the phone, Stripe and Zoom with keys), and there's no persistence beyond files. That is the pilot's job. | F12 |
| 12 | Why three builds? | We built three versions in parallel, attacked them with our own red-team agents, and merged the best ideas. All three passed the 7 checks. | F07, F17 |
| 13 | How is this different from Copilot or Glean? | I won't speak for their products. Here's what you saw live: memory holds only what a person approved. The role filter runs in code before the model sees anything. And it phones you, but never acts without a tap. | F05 |
| 14 | Can anyone just pick "CFO" in the picker? | In the demo, yes: the picker stands in for a company login (named as a limit). The rules after login are in code. | F05 |
| 15 | Does data leave the EU? | The AI runs on Google Vertex AI on the global location today; an EU region is a setting for a real deployment. | F13 |
| 16 | Does it work in Italian? | The model reads Italian; our demo data is mostly English. Not tested in Italian yet. | — |
| 17 | When does it decide to call? | Only when the model says the email is urgent AND the code finds urgency words; never for a suspicious email; once per email. | F10, F05 |
| 18 | What would the pilot with Ariete look like? | One client firm, read-only copies of their tools, a few weeks, and a person approving every fact and action. Terms to agree together. | F14 |
| 19 | Who has time to approve everything? | Each area has one owner (finance by the CFO), and only facts or actions that need a decision reach them. | F05 |
