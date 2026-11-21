# Billing readiness after a customer corrects acceptance

Finance or the COO is the proposed buyer at a fixed-fee implementation firm. Head of Delivery is the proposed champion. The measurable outcome is time to an accurate, invoice-ready handoff. Issuance, payment and customer communication stay in the firm's systems.

## One-minute workspace replay

Use **Jury checklist → Open Orchard handoff** on a fresh instance. The replay loads a historical approval by Giulia. It uses four synthetic customer emails from `billing_examples/`; the coordinator’s milestone, version and accepted scope annotations drive the hold. The delivery task is a separate source.

| Stage time | Click and visible result |
|---|---|
| 0–12 s | Expand **Read draft · Orchard finance handoff · A+B**. Its citations open the accepted customer email and the delivery-ready task. Leave it pending. |
| 12–22 s | In the message selector, simulate the ordinary follow-up and forwarded duplicate. Approvals still shows the same pending handoff. |
| 22–40 s | Simulate **Customer correction · Site A only**. The receipt shows the approved A+B email beside the corrected email. Finance is already on hold and Giulia is the named reviewer. Open either source chip. |
| 40–50 s | As Giulia, click **Replace the record**. In Approvals the original draft is closed and the fresh Site A draft cites the correction and delivery task. |
| 50–60 s | Click **Approve to mock outbox** on the fresh draft. Open Outbox to show the single internal Site A handoff. |

Run `../../.venv/bin/python billing_shadow.py` from this directory for the same endpoint replay. If Giulia rejects the correction while A+B is still active, the original handoff returns to pending. Invoice issuance and customer communication remain in the firm’s systems.

**Plain-text trial.** A separate synthetic message paraphrased the correction without the fixture annotations. Vertex Gemini 3.8 Flash identified Site A, Site B’s outstanding testing and the conflict with the correct Orchard decision in 12.73 seconds. The original draft remained pending. The verified automatic hold uses annotated replay inputs. No real customer milestone or time savings have been measured.

## Incumbent comparison on that same case

| Alternative | What the evidence supports | Trial still needed |
|---|---|---|
| Rocketlane | Its documentation describes milestone-triggered draft or in-review invoices, assigned approval permissions, and replies to project updates flowing into project conversations. [Billing schedules](https://help.rocketlane.com/support/solutions/articles/67000747137-understanding-billing-schedules-and-events) · [Approval permissions](https://help.rocketlane.com/support/solutions/articles/67000749237-managing-invoicing-permissions-in-rocketlane) · [Email replies](https://help.rocketlane.com/support/solutions/articles/67000717358-how-to-share-project-updates-from-your-projects-in-rocketlane) | In a configured tenant, send the correction in a new thread after preparation. Observe whether it attaches to this milestone, identifies the reviewer and holds release automatically. No tenant trial yet. |
| Firm's tracker or spreadsheet | No customer workbook or tracker has been observed. | Have the coordinator replay the same case using their current columns, links, owner and Finance queue. Count manual transfers and check whether Finance can release an old copy. |
| Configured incumbent workflow | A plausible alternative maps a change in the milestone field to a review task. Rocketlane documents task and field triggers. [Automation documentation](https://help.rocketlane.com/support/solutions/articles/67000722958-introduction-to-automations) | Let the firm’s admin configure its preferred workflow. Repeat with an unrelated follow-up and an old forwarded duplicate. Record setup time, manual reconciliation and actual release behavior. |

## Interview and paired replay

Recruit 8–10 fixed-fee implementation firms that bill by milestone. Ask Finance and Delivery to walk through the same recent case using redacted records.

1. “Show the last milestone where the invoice handoff was delayed, paused or prepared on the wrong basis. What happened next?” Record dates from acceptance, delivery-ready status, draft and final Finance handoff.
2. “Open the acceptance and the later thread. Which project record linked them? Who could decide? What did Finance see when it tried to release the original handoff?” Observe the clicks and copies.
3. “Show another recent occurrence and a normal follow-up that should proceed. Who did the reconciliation and how many active minutes did it take?” Separate observed time from recall.
4. Replay the same redacted cases in the current setup and in shadow mode. Have a reviewer unfamiliar with each case identify the governing email, scope, decision owner and release basis. Record correctness and time.
5. Ask Delivery to nominate an upcoming real milestone. Ask Finance or the COO for a dated pilot decision, sponsor, scope and amount they would authorize.

Measure elapsed acceptance-to-ready time and coordinator active minutes per milestone in both workflows. Count unnecessary holds over all reviewer-adjudicated nonmaterial messages, missed holds over material corrections, and correctly reconstructed cases over all reviewed. Record duplicates separately. Present sample sizes and individual case differences.

**Validation gate:** proceed only after three firms show repeated recent cases, two agree to trial on real work and a budget holder commits to a paid pilot. Interviews completed: 0. Customer artifacts observed: 0. Paid commitments: 0. The pilot demonstrates behavior on synthetic evidence. Commercial demand and the incumbent gap remain open.
