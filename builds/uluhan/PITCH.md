# Filare Labs · three-minute click track

Before the timer, reset, select Luca and run the simulated 08:30 sweep. Wait for seven role-specific briefs. The header shows the current mode. Open a result’s trace to identify the mode that produced it. Vertex sends model calls externally and can fall back per run. The deterministic fallback runs locally. All identities and emails are synthetic and deliveries use a mock outbox.

| Time | Click and show | Spoken cue |
|---|---|---|
| 0:00–0:22 | Open Luca’s Brain DM. Point to the €14,640 second notice and its evidence. | “We simulated the morning scheduler before coming on stage. It read the overnight items and prepared a separate brief for each colleague.” |
| 0:22–0:42 | Luca → Outbox (empty) → Approvals → Read draft → Approve to mock outbox → Outbox. | “Luca approved this invoice review request. One entry appears in his mock outbox.” |
| 0:42–1:07 | Checklist → Review as Sara → approve mem-p01, reject mem-p02 → checklist rollout shortcut. Open its citation and close. | “Sara accepted the rollout evidence and rejected the contract estimate. The answer opens the field team’s message.” |
| 1:07–1:30 | Checklist runway shortcuts, first Giulia then Sara. Ask about Wi-Fi. Open Morning email. | “Finance sees seven months with evidence. Tech gets an abstention. The missing Wi-Fi password also gets an abstention. This is Sara’s same brief in email form.” |
| 1:30–2:03 | Change control → Ask as Giulia → open mem-001 (email-005). Select Sara, simulate archived email, reject €12,000. Repeat Ask as Giulia. Open Approvals and expand Confirm Q1 2027 cloud budget. Leave it pending. | “The approval email establishes €18,000. Rejecting an older estimate preserves it. Giulia has a draft quoting that specific approval.” |
| 2:03–2:15 | Introduce the proposed application during the transition into the final sequence. | “In investor onboarding, the same rule applies when someone reviews a document and a corrected version arrives before signature. The next action needs review against the corrected evidence.” |
| 2:15–2:32 | Checklist → Simulate newer €25,000 claim as Sara. Show both sources and named reviewers. Switch to Giulia → Replace the record. | “Sara can inspect the claim. Giulia can approve it. The receipt marks €25,000 active and €18,000 superseded.” |
| 2:32–2:45 | Ask as Giulia again. Click the new citation, close, reopen the archived receipt. | “Same question. The answer cites the new decision. Sara’s €12,000 rejection is still on record.” |
| 2:45–3:00 | Giulia → Approvals → approve the €18,000 confirmation → Needs review. Open Giulia’s empty Outbox. | “The draft cites the superseded decision. Release checks that citation again. Nothing from Giulia went to the outbox.” |

Times are stage allocations. Before the pitch, prepare a second instance with `BRAIN_MODE=offline`. Complete the sweep, reject the archive as Sara, ask the budget question as Giulia and leave her €18,000 confirmation pending. Park on Jury checklist. If Vertex stalls, switch tabs, say “This is the deterministic fallback,” and resume at the newer-claim trigger. Close on the blocked draft and Giulia’s empty outbox. A private or EU-first deployment is a possible architecture. The investor-onboarding example is a proposed application. Ariete’s earlier private-beta listing does not establish its current capabilities or an endorsement.

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
