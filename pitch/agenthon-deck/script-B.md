# Script: Jarvis · Version B (PoliPrep problem, Filare demo)
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
- **Headline:** A tutor misses tomorrow's class. / Fourteen students don't know yet.
- **On slide:**
  - PoliPrep: one founder, a few tutors, one media person
  - 14 students in Cohort 1. One email in one inbox.
  - Our demo: a fictional scenario on Ariete's public services, no real student data
- **Visual:** one phone with an unread email, a class tile "tomorrow 09:00"
- **Sources:** F16, F20, F22 (footer: "A typical scenario, not a real incident · PoliPrep internal: team (Oct 2026); Cohort 1 = 14 of 20 places (8 Nov 2026)")
- **Say:** I run PoliPrep, an admission-test school: one founder, a few tutors, one media person. Picture this: a tutor can't make tomorrow's class. The email sits in one inbox. Fourteen students depend on someone noticing. Today I show it on a fictional scenario built on Ariete's own services, with the same problem: an urgent client email that landed with the account manager.

## 03 · Solution
- **Kicker:** How it works
- **Headline:** It reads everything. / People decide what it remembers.
- **On slide:**
  - Reads email, chat, tasks and docs (demo copies today), and Stripe
  - Proposes facts. A person approves.
  - Answers only from approved facts, with sources
  - Drafts actions and Zoom meetings. Nothing happens without a yes.
- **Visual:** the How-it-works diagram (Reads → Guard → A person approves → Answers & proposes)
- **Sources:** F05, F12
- **Say:** Jarvis reads the team's tools and proposes facts. A person approves them. It answers only from those, with sources. Nothing leaves without a yes.

## 04 · Live demo
- **Kicker:** Live demo
- **Headline:** Watch it speak first, say "I don't know", and call me.
- **On slide:**
  - 08:00 · the brief nobody asked for
  - "I don't know"
  - An urgent email · my phone rings
- **Visual:** the app on screen; this slide is only the bridge into the demo
- **Sources:** F03, F10
- **Say:** Let me show you. It's eight in the morning. Nobody asked, but each person already has a morning brief. Here, it proposed two facts. One is right, one has the wrong number. I approve one and reject the other. Now it answers, with the source. Same question about a client's unpaid invoice: the CFO gets the answer, the CTO gets "not for your role". The Wi-Fi password is nowhere, so Jarvis says "I don't know". Now a rival's attack: a fake CEO asks for an urgent payment. Blocked. And now something urgent arrives. My phone is ringing. That's Jarvis. (Answer on speaker, ask "What happened?", then say "Approve it.") It won't approve by phone. Back in the app, the action waits for one tap. I tap it. Only now does it happen.

## 05 · What we built and tested
- **Kicker:** Built and tested today
- **Headline:** Rival teams will try to break it. / The rules live in code.
- **On slide:**
  - 7 of 7 jury checks, enforced in code
  - 63 automated tests
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
  - Already connected: Stripe, Zoom, a real phone line
  - Next: Gmail, Slack, Notion, with the same rules
  - AI runs on Google Vertex AI; finance facts never go to the voice provider
  - About $0.003 per morning brief
  - First buyers: small firms, through partners like Ariete (pilot)
  - Market size: not estimated yet
- **Visual:** connector row, "today" vs "next"
- **Sources:** F11, F12, F13, F14 (footer: "Demo data; live connectors: phone, and Stripe and Zoom with keys · cost measured on build arif, 21 Nov 2026")
- **Say:** Stripe, Zoom and a real phone line already work. Today, a morning brief costs a third of a cent. The first buyers are small firms, through partners like Ariete. We haven't sized the market yet.

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
- **Say:** We built three versions in parallel and merged the best ideas. Ariete builds AI agents for professional firms. Let's pilot Jarvis with one of your clients. Because a colleague you trust says "I don't know", and "May I?"
