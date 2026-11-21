# Company Brain — three-minute jury pitch

All companies, people, clients, amounts, messages, and addresses shown below are fictional demo data. Before the timer, click **Reset**, select **Luca Bianchi · Accountant**, and open **🏁 Jury checklist**. Keep the browser zoomed so the checklist and Agent trace are both visible.

## 3-minute spoken script and click track

### 0:00–0:20 — Problem

**Say exactly:**

> “In a small company, the fact that matters is often buried in somebody else’s inbox. One person sees an overdue invoice, another sees a customer outage, and an old estimate can quietly overwrite an approved decision. A normal chatbot waits to be asked—and often trusts the last message it read.”

**Exact click:** None. Point to the seven numbered cards in **🏁 Jury checklist**.

### 0:20–0:35 — One-liner

**Say exactly:**

> “Company Brain is the colleague who speaks first, answers only from memory the team approved, and asks before it acts. It is built for Filare Labs, a fictional Torino sensor company, using entirely synthetic demo data.”

**Exact click:** Click **Run morning sweep** on checklist item 1.

### 0:35–2:15 — Live demo: seven checks, then change control

#### 0:35–0:47 — Checks 1 and 6: speaks first; only proposes

**Say exactly:**

> “Nobody asked a question. The scheduled sweep speaks first: Luca sees the EUR 14,640 second notice, with evidence, and a draft—not a sent email.”

**Exact clicks:** After the sweep opens **🧠 Brain**, click **✅ Approvals** in the left navigation; click **📤 Outbox** and show **Empty**; click **✅ Approvals** again; click **Approve to mock outbox** on the SensorParts draft; click **📤 Outbox**.

**Say exactly:**

> “The outbox was empty until Luca approved. Even now this is explicitly a mock outbox: nothing leaves the demo.”

#### 0:47–1:04 — Check 2: people curate memory

**Exact clicks:** In **Viewing as**, select **Sara Conti · Backend engineer**; click **📚 Memory review**; on `mem-p01`, click **Approve**; on `mem-p02`, click **Reject**; click **🧠 Brain**; click the suggestion **When does the Langhe fix roll out?**

**Say exactly:**

> “People, not the model, curate shared memory. Sara approves the sourced rollout plan and rejects the wrong EUR 83,000 extraction. Now the answer is Thursday 26 November at 07:00, sourced to the approved item.”

#### 1:04–1:21 — Checks 3 and 4: role-aware and cited

**Exact clicks:** In **Viewing as**, select **Giulia Ferrero · CFO**; click the suggestion **What is our cash runway?**; click its citation chip **📎 mem-002 · Cash runway and net burn** to open `email-003`; click **Close**; select **Sara Conti · Backend engineer**; click the suggestion **What is our cash runway?**

**Say exactly:**

> “The same runway question gives Giulia the approved seven-month answer and opens the underlying email. Sara gets ‘I don’t know’—not even restricted finance metadata reaches her model or trace.”

#### 1:21–1:31 — Check 5: admits gaps

**Exact clicks:** Click the **Ask the brain…** field, type **What is the office Wi-Fi password?**, then click **Ask**.

**Say exactly:**

> “For a genuine gap, it says ‘I don’t know’ and shows no citation. A plausible guess is still a failure.”

#### 1:31–1:40 — Check 7: fits the team’s day

**Exact clicks:** Click **📧 Morning email**, then click **🧠 Brain**.

**Say exactly:**

> “The same role-filtered, cited brief meets the team as a direct message or a morning email—not as another dashboard to remember.”

#### 1:40–2:15 — Climax: change control and Decision Receipt

**Exact clicks:** In the top **✉ Simulate incoming email…** menu, select **Archived cloud budget email**. In the resulting Brain alert, point first to **Company record · approved**, then **Incoming claim · not approved**, then **Decision receipt**, **Can decide**, and **✓ Company record unchanged**. Select **Giulia Ferrero · CFO** in **Viewing as**; click the suggestion **What is the Q1 2027 cloud budget?**; click the citation chip **📎 mem-001 · Q1 2027 cloud budget**.

**Say exactly:**

> “Here is the signature moment. An archived email claims EUR 12,000, but the approved decision is EUR 18,000. Most assistants believe the last thing they read. Ours treats the email as a claim, places both versions side by side, names Giulia, Marco, and Elena as the authorized reviewers, and issues a Decision Receipt: older evidence cannot replace the newer approval, so the company record is unchanged. I ask the budget now: EUR 18,000, cited to the approved record and its source.”

### 2:15–2:45 — Feasibility and honest limits

**Exact click:** Click the newest **ask** run in **Agent trace** and point to the tool steps, token counts, cost, and mode label.

**Say exactly:**

> “This is one FastAPI service. A measured full seven-check demo on Vertex AI in the EU cost between ten and thirteen US cents. Access filtering, citation validation, abstention, approval, and change authority are enforced in code, outside the prompt. Humans approve every memory change and outgoing draft. For production we still need real authentication, persistent storage, connectors, a retention policy, a GDPR DPIA, and an Italian Article 4 workplace-monitoring review. Those are open items, not hidden claims.”

### 2:45–3:00 — Closing

**Exact click:** Return to **🏁 Jury checklist** and leave the seven checks plus the star moment visible.

**Say exactly:**

> “A company does not need an AI that sounds certain. It needs a colleague it can trust: one who speaks first, shows its evidence, says ‘I don’t know,’ and asks ‘may I?’ Company Brain changes knowledge by decision—not by inbox.”

## 30-second fallback if the live demo fails

If Vertex calls fail but the service still responds, point to the header pill **Offline fallback (no model)**. Do not describe that run as live Vertex. Click **🏁 Jury checklist**, click **Simulate archived email**, then click **Ask as Giulia** on the change-control card. If the page itself is unavailable, make no clicks and do not claim a live result.

**Say exactly:**

> “The live model connection has failed, so the product has switched to its clearly labelled offline fallback; I will not present that as Vertex. The safety behavior remains deterministic: an archived EUR 12,000 email becomes a reviewable claim, never an approved fact; the Decision Receipt keeps the authorized EUR 18,000 record; unsupported questions return ‘I don’t know’; and no draft can leave without a named person’s approval. The full demo is measured at ten to thirteen US cents, and the code path is covered by sixty-six automated tests.”

## Likely jury questions

1. **Is this really agentic, or just chat over documents?**  
   The scheduled `/api/sweep` runs before any question, produces role-specific briefs, and can create a review draft from approved evidence. The ask, brief, and ingest agents use tools, while the UI exposes their trace.

2. **Can Sara ask the model to reveal finance data?**  
   No finance facts are sent to her model: `Store.access`, `can_see`, `visible_memory`, and `t_read_source` filter by group before a model call. Ask-run traces are also visible only to the person who triggered them.

3. **What stops a confident but wrong answer with a real-looking citation?**  
   `t_answer` accepts only visible, approved evidence and application code renders the stored approved fact; an unrelated valid citation cannot authorize invented answer text. If matching is unsupported or tied, `confident_match` returns the coded “I don’t know” path.

4. **Can the agent approve memory or send an email by itself?**  
   No agent tool can approve, send, or change a decision. Separate HTTP approval endpoints check the designated person, and approval writes only to the local mock outbox in this prototype.

5. **Why does the archived EUR 12,000 email not win?**  
   It becomes a candidate beside `mem-001`, not an overwrite. `replays_current_evidence`, `fact_reviewers`, and `_decide_memory` enforce both chronology and authority, while `decision_receipt` explains the unchanged EUR 18,000 record.

6. **What happens with a prompt-injection email?**  
   Incoming bodies are marked untrusted, the injection pattern is flagged, and suspicious sources cannot create memory. The code also excludes the suspicious sender from permitted draft recipients; nothing is approved or sent.

7. **What happens if Vertex or the venue Wi-Fi fails?**  
   A circuit breaker falls back to a deterministic offline planner and the UI labels it **Offline fallback (no model)**; the trace records the fallback. The offline path preserves the same access, citation, abstention, and approval guards.

8. **Is this production-ready, and what would deployment cost?**  
   Not yet: identity is a demo picker, data is in memory, connectors are synthetic, and the outbox is mocked; authentication, persistence, retention, GDPR DPIA, and Article 4 review remain open. The measured live full demo cost USD 0.10–0.13 on Vertex AI in the EU, and a single question measured about USD 0.001–0.004.
