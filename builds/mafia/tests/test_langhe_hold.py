"""The Langhe Viva approval hold, the quarter/year guard and the Friday control.

    python -m unittest discover -s builds/mafia/tests -q

Everything here runs offline (no Gemini): the sender checks, the timing comparison and the role filter are code.
"""
import http.client
import json
import os
import socket
import sys
import threading
import unittest
from pathlib import Path

os.environ["BRAIN_PERSIST"] = "off"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app  # noqa: E402
import brain as B  # noqa: E402


def customer_reply(b):
    """Paolo's waiting reply to the Langhe customer, created by the morning sweep."""
    return next(a for a in b.actions.values()
                if a["kind"] == "email" and a["approver"] == "paolo" and a["to"] == "agronomo@langheviva.example")


class WednesdayHold(unittest.TestCase):
    def test_baseline_reply_is_approvable_before_the_warning(self):
        b = B.Brain(model=None)
        b.sweep()
        draft = customer_reply(b)
        self.assertEqual(draft["status"], "waiting")
        b.decide_action("paolo", draft["id"], "approve")
        self.assertEqual([o["to"] for o in b.outbox], ["agronomo@langheviva.example"])

    def test_warning_holds_the_reply_and_refuses_a_stale_approval(self):
        b = B.Brain(model=None)
        b.sweep()
        draft = customer_reply(b)
        b.ingest("email-101")
        # exactly one hold and exactly one waiting internal request, both for this case
        self.assertEqual([a["id"] for a in b.actions.values() if a["status"] == "held"], [draft["id"]])
        internal = [a for a in b.actions.values() if a["status"] == "waiting" and a["approver"] == "paolo"]
        self.assertEqual(len(internal), 1)
        self.assertEqual(internal[0]["to"], "davide")
        # the outbox is empty, a stale approval is refused, and it stays empty
        self.assertEqual(b.outbox, [])
        with self.assertRaises(ValueError):
            b.decide_action("paolo", draft["id"], "approve")
        self.assertEqual(b.outbox, [])
        # the held card names the incoming email and the engineering source that caused the hold
        self.assertEqual(draft["hold_sources"], ["email-101", "chat-003"])
        self.assertEqual(draft["evidence"], [
            {"text": "Customer needs coverage Wednesday night", "cites": ["email-101"]},
            {"text": "Engineering rollout scheduled Thursday, 07:00", "cites": ["chat-003"]},
        ])
        self.assertIn("email-101", draft["hold_reason"])
        self.assertTrue(any(e["event"] == "held draft" for e in b.log))

    def test_paolo_approves_the_internal_request_to_davide(self):
        b = B.Brain(model=None)
        b.sweep()
        b.ingest("email-101")
        internal = next(a for a in b.actions.values() if a["status"] == "waiting" and a["approver"] == "paolo")
        with self.assertRaises(PermissionError):
            b.decide_action("davide", internal["id"], "approve")   # only the named approver
        b.decide_action("paolo", internal["id"], "approve")
        self.assertEqual([o["to"] for o in b.outbox], ["davide"])
        with self.assertRaises(ValueError):                        # a second approval is refused
            b.decide_action("paolo", internal["id"], "approve")
        self.assertEqual(len(b.outbox), 1)

    def test_unrelated_work_is_untouched_and_a_replay_changes_nothing(self):
        b = B.Brain(model=None)
        b.sweep()
        rollout = (b.tasks["task-001"]["status"], b.tasks["task-001"]["due"])
        b.ingest("email-101")
        with self.assertRaises(ValueError):                        # the app's own duplicate-delivery response
            b.ingest("email-101")
        self.assertEqual(sum(1 for a in b.actions.values() if a["status"] == "held"), 1)
        self.assertEqual(sum(1 for a in b.actions.values() if a["status"] == "waiting" and a["approver"] == "paolo"), 1)
        self.assertEqual((b.tasks["task-001"]["status"], b.tasks["task-001"]["due"]), rollout)  # the plan stands
        self.assertEqual(next(a for a in b.actions.values() if a["approver"] == "luca")["status"], "waiting")


class HeldDraftOverHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            cls.port = s.getsockname()[1]
        cls.brain = B.Brain(model=None)
        cls.brain.sweep()
        cls.brain.ingest("email-101")
        cls.server = app.make_server(cls.port, cls.brain)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def post(self, path, body):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("POST", path, body=json.dumps(body).encode(),
                  headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.port}"})
        r = c.getresponse()
        return r.status, json.loads(r.read() or b"{}")

    def test_the_approval_endpoint_refuses_a_held_draft(self):
        draft = next(a for a in self.brain.actions.values() if a["status"] == "held")
        status, body = self.post("/api/action", {"user": "paolo", "id": draft["id"], "decision": "approve"})
        self.assertEqual(status, 400)
        self.assertIn("held", body["error"].lower())
        self.assertEqual(self.brain.outbox, [])


class FridayControl(unittest.TestCase):
    def test_a_later_need_is_not_a_conflict(self):
        b = B.Brain(model=None)
        b.sweep()
        draft = customer_reply(b)
        b.ingest("email-105")
        self.assertEqual(draft["status"], "waiting")               # still reviewable, not held
        self.assertEqual([a for a in b.actions.values()
                          if a["status"] == "waiting" and a["approver"] == "paolo"], [draft])  # no escalation
        b.decide_action("paolo", draft["id"], "approve")
        self.assertEqual([o["to"] for o in b.outbox], ["agronomo@langheviva.example"])


class QuarterYearGuard(unittest.TestCase):
    def test_offline_a_wrong_period_is_not_answered(self):
        b = B.Brain(model=None)
        m = b.ask("giulia", "What is the Q1 2027 cloud budget?")
        self.assertEqual((m["status"], m["cites"]), ("answered", ["mem-001"]))
        self.assertIn("18,000", m["text"])
        for q in ("What is the Q1 2032 cloud budget?", "What is the Q1 2026 cloud budget?"):
            r = b.ask("giulia", q)
            self.assertEqual(r["status"], "unknown", q)
            self.assertEqual(r["cites"], [])
            self.assertNotIn("18,000", r["text"])

    def test_gemini_citation_must_name_the_asked_period(self):
        def model(system, prompt):
            info = {"mode": "gemini", "model": "fake", "ms": 1, "cost_usd": 0}
            if "answer a colleague" in system:
                q = prompt.split("Question from")[-1]
                year = "2032" if "2032" in q else "2027"
                return {"answer": f"The Q1 {year} cloud budget is EUR 18,000.", "cites": ["mem-001"]}, info
            return None, info

        b = B.Brain(model=model)
        self.assertEqual(b.ask("giulia", "What is the Q1 2027 cloud budget?")["status"], "answered")
        bad = b.ask("giulia", "What is the Q1 2032 cloud budget?")
        self.assertEqual(bad["status"], "unknown")                 # same citation, wrong period: refused
        self.assertEqual(bad["cites"], [])


class RunwayRoleFilter(unittest.TestCase):
    def test_giulia_gets_the_answer_and_sara_does_not(self):
        b = B.Brain(model=None)
        g = b.ask("giulia", "What is our cash runway?")
        self.assertEqual(g["cites"], ["mem-002"])
        self.assertIn("412", g["text"])
        s = b.ask("sara", "What is our cash runway?")
        self.assertNotIn("412", s["text"])
        self.assertEqual(s["cites"], [])


if __name__ == "__main__":
    unittest.main()
