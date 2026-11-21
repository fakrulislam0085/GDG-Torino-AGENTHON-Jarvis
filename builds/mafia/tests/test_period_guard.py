"""The quarter/year evidence guard (Check 5): an answer must be about the period the person asked for.

An explicit "Qn YYYY" in the question only matches a fact that names that same quarter and year together.
A real 2027 citation, or a 2026 approval date inside the fact, does not qualify for a Q1 2032 or Q1 2026 ask.

    python -m unittest discover -s builds/mafia/tests -q
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import brain as B  # noqa: E402


def budget_model(answer="The Q1 2027 cloud budget is EUR 18,000.", cites=("mem-001",)):
    """A scripted 'Gemini' that answers every budget question by citing the genuine 2027 fact."""
    def model(system, prompt):
        info = {"mode": "gemini", "model": "fake", "ms": 1, "cost_usd": 0}
        if "answer a colleague" in system:
            if "budget" in prompt.split("Question from")[-1]:
                return {"answer": answer, "cites": list(cites)}, info
            return {"answer": "I don't know.", "cites": []}, info
        return None, info
    return model


class PeriodParsing(unittest.TestCase):
    def test_explicit_quarter_year_is_recognised(self):
        self.assertEqual(B.quarter_years("What is the Q1 2032 cloud budget?"), {(1, 2032)})
        self.assertEqual(B.quarter_years("cloud budget for Q2-2027"), {(2, 2027)})
        self.assertEqual(B.quarter_years("Q4 of 2026 spend"), {(4, 2026)})
        self.assertEqual(B.quarter_years("q1 2027 and Q1 2032"), {(1, 2027), (1, 2032)})

    def test_a_bare_four_digit_number_is_not_a_period(self):
        for text in ("What is the 2032 cloud budget?", "budget approved on 18 Nov 2026", "invoice INV-2026-0912"):
            self.assertEqual(B.quarter_years(text), set(), text)

    def test_a_fact_supports_only_its_own_quarter_and_year(self):
        fact = "Q1 2027 cloud budget is EUR 18,000, approved by Giulia on 18 Nov 2026."
        self.assertTrue(B.period_supported(fact, {(1, 2027)}))
        self.assertFalse(B.period_supported(fact, {(1, 2032)}))
        self.assertFalse(B.period_supported(fact, {(1, 2026)}))  # the 2026 approval date is not a period
        self.assertFalse(B.period_supported(fact, {(2, 2027)}))
        self.assertTrue(B.period_supported("no period named here", set()))  # nothing requested -> unrestricted


class OfflineGuard(unittest.TestCase):
    def setUp(self):
        self.b = B.Brain(model=None)

    def test_q1_2027_is_answered_with_the_approved_citation(self):
        m = self.b.ask("giulia", "What is the Q1 2027 cloud budget?")
        self.assertEqual(m["status"], "answered")
        self.assertEqual(m["cites"], ["mem-001"])
        self.assertIn("18,000", m["text"])

    def test_q1_2032_gets_idk_without_a_wrong_period_citation(self):
        m = self.b.ask("giulia", "What is the Q1 2032 cloud budget?")
        self.assertEqual((m["status"], m["cites"]), ("unknown", []))
        self.assertTrue(m["text"].startswith("I don't know"))
        self.assertNotIn("18,000", m["text"])
        self.assertNotIn("2027", m["text"])

    def test_q1_2026_is_not_satisfied_by_a_2026_approval_date(self):
        m = self.b.ask("giulia", "What is the Q1 2026 cloud budget?")
        self.assertEqual((m["status"], m["cites"]), ("unknown", []))
        self.assertNotIn("18,000", m["text"])

    def test_a_supported_paraphrase_still_answers(self):
        m = self.b.ask("giulia", "How much is the cloud budget for Q1 2027?")
        self.assertEqual(m["status"], "answered")
        self.assertEqual(m["cites"], ["mem-001"])


class GeminiCitationGuard(unittest.TestCase):
    def test_a_real_2027_citation_for_2032_is_refused(self):
        b = B.Brain(model=budget_model())
        m = b.ask("giulia", "What is the Q1 2032 cloud budget?")
        self.assertNotEqual(m["status"], "answered")
        self.assertEqual(m["cites"], [])
        self.assertNotIn("18,000", m["text"])
        self.assertNotIn("2027", m["text"])

    def test_a_real_2027_citation_for_2027_is_shown(self):
        b = B.Brain(model=budget_model())
        m = b.ask("giulia", "What is the Q1 2027 cloud budget?")
        self.assertEqual(m["status"], "answered")
        self.assertEqual(m["cites"], ["mem-001"])
        self.assertIn("18,000", m["text"])


class PermissionsAndMemoryDemoStillWork(unittest.TestCase):
    def setUp(self):
        self.b = B.Brain(model=None)

    def test_runway_role_split_is_unchanged(self):
        g = self.b.ask("giulia", "What is our cash runway?")
        self.assertEqual(g["status"], "answered")
        self.assertEqual(g["cites"], ["mem-002"])
        s = self.b.ask("sara", "What is our cash runway?")
        self.assertNotIn("412", s["text"])
        self.assertEqual(s["cites"], [])

    def test_rollout_memory_demo_after_approval(self):
        q = "When does the Langhe fix roll out?"
        self.assertEqual(self.b.ask("davide", q)["status"], "pending")
        self.b.review_memory("davide", "mem-p01", "approve")
        m = self.b.ask("davide", q)
        self.assertEqual((m["status"], m["cites"]), ("answered", ["mem-p01"]))
        self.assertIn("26 Nov", m["text"])


if __name__ == "__main__":
    unittest.main()
