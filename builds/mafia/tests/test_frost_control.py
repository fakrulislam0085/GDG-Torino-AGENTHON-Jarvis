"""The frost-deadline counterexample for the Langhe Viva demo.

Two customer emails sound equally urgent and carry the same engineering plan; only the
forecast date differs. The Brain's own date comparison (the timing rule lives in the app,
never in this test) decides the outcome:

  * Wednesday 25 Nov forecast vs the Thursday 26 Nov 07:00 rollout -> the old customer
    reply is HELD and one internal request to move the repair up waits for Paolo.
  * Friday 27 Nov forecast vs the same rollout -> the customer reply stays reviewable, no
    request to move the repair up is created, and the result only describes the scheduled
    rollout (it makes no promise of restoration).

The test drives the normal intake path (Brain.ingest -> _ingest_spec) and reads only public
state, so it passes on Agent 1's comparison and fails on a build that has no comparison.

    python -m unittest discover -s builds/mafia/tests -q
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import brain as B  # noqa: E402

CUSTOMER = "agronomo@langheviva.example"
ENGINEER = "davide"
WEDNESDAY = "email-101"
FRIDAY = "email-105"
STATUS_SCHEDULED = "Rollout is scheduled before the forecast. Restoration is unconfirmed."


def clean_state():
    """A fresh demo: the morning sweep already created the drafts (incl. the customer reply)."""
    b = B.Brain(model=None, persist=False)
    b.sweep()
    return b


def emails_to(b, address):
    return [a for a in b.actions.values()
            if a["kind"] == "email" and a["to"] == address and a["status"] != "rejected"]


def customer_reply(b):
    return next((a for a in emails_to(b, CUSTOMER)), None)


def requests_to_move_repair_up(b):
    """The internal escalation draft is addressed to the engineer (Davide)."""
    return emails_to(b, ENGINEER)


def public_text(b):
    chunks = [json.dumps(b.alerts, ensure_ascii=False)]
    chunks += [json.dumps(b.dms[pid], ensure_ascii=False) for pid in b.people]
    chunks.append(json.dumps(list(b.actions.values()), ensure_ascii=False))
    chunks.append(json.dumps(b.runs, ensure_ascii=False))
    chunks.append(json.dumps(b.log, ensure_ascii=False))
    return "\n".join(chunks)


class FrostDeadlineControl(unittest.TestCase):
    def test_wednesday_forecast_before_rollout_holds_the_customer_reply(self):
        b = clean_state()
        b.ingest(WEDNESDAY)
        reply = customer_reply(b)
        self.assertIsNotNone(reply, "the old customer reply draft should exist after the sweep")
        self.assertEqual(reply["status"], "held",
                         "Wed 25 Nov forecast is before the Thu 26 Nov 07:00 rollout: hold the customer reply")
        escalations = requests_to_move_repair_up(b)
        self.assertEqual(len(escalations), 1, "exactly one internal request to move the repair up")
        self.assertEqual(escalations[0]["approver"], "paolo", "that request waits for Paolo")
        self.assertEqual(escalations[0]["status"], "waiting")
        self.assertEqual(b.outbox, [], "nothing is sent automatically")

    def test_friday_forecast_after_rollout_keeps_the_reply_reviewable(self):
        b = clean_state()
        b.ingest(FRIDAY)
        reply = customer_reply(b)
        self.assertIsNotNone(reply)
        self.assertEqual(reply["status"], "waiting",
                         "Fri 27 Nov forecast is after the rollout: the reply stays reviewable")
        self.assertEqual(requests_to_move_repair_up(b), [], "no request to move the repair up")
        self.assertEqual(b.outbox, [], "nothing is sent automatically")
        text = public_text(b)
        self.assertIn(STATUS_SCHEDULED, text,
                      "the Friday result must describe the scheduled rollout")
        low = text.lower()
        for promise in ("will be restored", "restored by friday", "restoration is confirmed"):
            self.assertNotIn(promise, low, "Friday must not promise the sensors will be restored")

    def test_only_the_deadline_separates_wednesday_from_friday(self):
        wed, fri = clean_state(), clean_state()
        wed.ingest(WEDNESDAY)
        fri.ingest(FRIDAY)
        self.assertNotEqual(customer_reply(wed)["status"], customer_reply(fri)["status"],
                            "same email, same urgency: only the deadline changes the outcome")
        self.assertEqual(len(requests_to_move_repair_up(wed)), 1)
        self.assertEqual(len(requests_to_move_repair_up(fri)), 0)

    def test_friday_fixture_is_the_wednesday_email_with_only_the_date_changed(self):
        b = clean_state()
        incoming = {i["id"]: i for i in b.extra["incoming"]}
        wed, fri = incoming[WEDNESDAY], incoming[FRIDAY]
        self.assertNotEqual(wed["id"], fri["id"], "the Friday forecast has its own input id")
        for field in ("from", "to", "cc", "acl"):
            self.assertEqual(wed[field], fri[field], f"{field} is preserved")
        for kept in ("-4 °C", "40 sensors", "Barbaresco", "Cantina Langhe Viva"):
            self.assertIn(kept, wed["body"])
            self.assertIn(kept, fri["body"])
        self.assertIn("Wednesday", wed["body"])
        self.assertIn("Friday", fri["body"])
        self.assertIn("25 November", wed["body"])
        self.assertIn("27 November", fri["body"])
        # the engineering plan is preserved verbatim in both candidate escalation drafts
        wed_draft = b.extra["offline"]["ingest"][WEDNESDAY]["proposals"][0]
        fri_draft = b.extra["offline"]["ingest"][FRIDAY]["proposals"][0]
        for draft in (wed_draft, fri_draft):
            self.assertIn("40 sensors on GW-07", draft["body"])
            self.assertIn("The firmware 2.3 rollout is planned for Thursday 07:00", draft["body"])


if __name__ == "__main__":
    unittest.main()
