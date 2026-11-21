# Script: Jarvis · Version A (Filare Labs story)
Status: APPROVED (founder, 21 Nov 2026)
Audience: AGENTHON jury, track Agentic AI for business · Decision: score us top 2 · Format: spoken 3 min
Ideas to remember (5): 1. Jarvis speaks first. 2. It only uses what people approved. 3. It says "I don't know". 4. It never acts without a yes, not even on the phone. 5. The rules live in code, so rivals can't talk it out of them.

## 01 · Cover
- **Kicker:** (none)
- **Headline:** Jarvis. / The colleague who knows, speaks first, and asks before it acts.
- **On slide:**
  - Token Mafia · Agentic AI for business · GDG Torino AGENTHON · 21 November 2026
- **Visual:** the voice orb, large, light background
- **Sources:** —
- **Say:** Hi, I'm Arif, from Token Mafia. This is Jarvis: a colleague that knows, speaks first, and asks before it acts.

## 02 · Problem
- **Kicker:** The problem
- **Headline:** Every company already has the answer. / It's in someone else's inbox.
- **On slide:**
  - Studio Rinaldi: 60 client files stuck before the 28 November deadline
  - Silvia and Lorenzo receive the urgent email. Jarvis alerts Francesca, the CEO, and prepares two proposals for her approval
  - Each person needs to know something different
  - Our demo: a fictional scenario on Ariete's public services
- **Visual:** one email card landing with Silvia (to) and Lorenzo (cc)
- **Sources:** F21, F22 (footer: "Fictional scenario built on Ariete Tech Solutions' public services. Not Ariete's data.")
- **Say:** Our demo company does what Ariete does: AI automations for professional firms. Studio Rinaldi has 60 client files stuck before the 28 November deadline. Silvia and Lorenzo receive the urgent email. Jarvis alerts Francesca, the CEO, and prepares two proposals for her approval. Each person needs to know something different, today.

## 03 · Solution
- **Kicker:** How it works
- **Headline:** It reads everything. / People decide what it remembers.
- **On slide:**
  - Reads email, chat, tasks and docs (demo copies today)
  - Proposes facts. A person approves.
  - Answers only from approved facts, with sources
  - Drafts messages and Zoom meetings. They wait for a yes.
- **Visual:** the How-it-works diagram (Reads → Guard → A person approves → Answers & proposes)
- **Sources:** F05, F12
- **Say:** Jarvis reads the team's tools and proposes facts. A person approves them. It answers only from those, with sources. Messages and meetings wait for a yes.

## 04 · Live demo
- **Kicker:** Live demo
- **Headline:** Watch it speak first, say "I don't know", and alert me.
- **On slide:**
  - 08:00 · the brief nobody asked for
  - "I don't know"
  - An urgent email · Jarvis alerts Francesca
- **Visual:** the app on screen (caption: "Synthetic Ariete-inspired demo"); this slide is only the bridge into the demo
- **Sources:** F03, F10
- **Say:** Let me show you. It's eight in the morning. Nobody asked, but Francesca already has her brief. Now the urgent email from Studio Rinaldi arrives. Jarvis can alert Francesca immediately: here is the call card. It has prepared two proposals for Lorenzo, an internal message and a Zoom meeting. They wait for her approval, and the outbox is empty. I approve only the internal message: one item lands in the mock outbox, and the Zoom proposal is still waiting. Memory: it proposed two facts. I approve one and reject the other, and the answer cites its source. Same question, "Has Bellini & Co. paid the pilot invoice?": the finance group and the CEO can read that fact, so Marta gets the answer with its source; Andrea, the CTO, is refused. The Wi-Fi password is nowhere, so Jarvis says "I don't know". (A real phone call is only part of the pitch if it was rehearsed on the stage laptop with setup and opt-in auto-dial.)

## 05 · What we built and tested
- **Kicker:** Built and tested today
- **Headline:** Rival teams will try to break it. / The rules live in code.
- **On slide:**
  - 7 of 7 jury checks, enforced in code
  - 76 automated tests pass (Filare data) + a separate Ariete rehearsal
  - Fake CEO payment: blocked
  - A reworded attack: caught by a second AI check
  - On the phone: no approvals. "Tap it in the app."
  - Our 3 attacker agents: all 3 builds still pass 7 of 7
- **Visual:** 6 short proof rows with check icons
- **Sources:** F05, F06, F07, F08, F09, F10 (footer: "Our tests and live runs, 21 November 2026")
- **Say:** So the rules live in code, not in the prompt. A reworded attack that our patterns missed was caught by a second AI check.

## 06 · Feasibility
- **Kicker:** Beyond the prototype
- **Headline:** Built for one company. / Ready for any firm.
- **On slide:**
  - In this demo: in-app call card, Zoom proposals, phone call (opt-in, needs setup). Stripe is off in the Ariete dataset.
  - Next: Gmail, Slack, Notion, with the same rules
  - AI runs on Google Vertex AI; the demo uses synthetic data only
  - About $0.003 per morning brief (measured on the earlier Arif build)
  - First buyers: small firms, through partners like Ariete (pilot)
  - Market size: not estimated yet
- **Visual:** connector row, "today" vs "next"
- **Sources:** F11, F12, F13, F14 (footer: "Demo data; live connectors: phone, and Stripe and Zoom with keys · cost measured on build arif, 21 Nov 2026")
- **Say:** In this demo, Jarvis alerts the CEO with an in-app call card, and proposes messages and Zoom meetings that wait for approval. A real phone call needs setup and opt-in. On our earlier build, a morning brief cost about a third of a cent. The first buyers are small firms, through partners like Ariete. We haven't sized the market yet.

## 07 · Team, ask and close
- **Kicker:** The ask
- **Headline:** Ariete: let's pilot Jarvis with one of your client firms.
- **On slide:**
  - Arif · founder, PoliPrep and Life At PoliTO
  - Hamid and Uluhan · engineering students, Politecnico di Torino
  - Three builds in parallel, the best ideas merged
  - A colleague you trust says "I don't know", and "May I?"
- **Visual:** three names, the closing line large
- **Sources:** F14, F17, F18, F19
- **Say:** I run PoliPrep, and I built Jarvis because I live this problem. We built three versions in parallel and merged the best ideas. Ariete builds AI agents for professional firms. Let's pilot Jarvis with one of your clients. Because a colleague you trust says "I don't know", and "May I?"
