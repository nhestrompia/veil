import unittest

from run_private_entry_attacks import guarded_verdict


class GuardedAttackTests(unittest.TestCase):
    def test_private_overlap_prevents_false_bypass(self):
        self.assertEqual(guarded_verdict({"newSubmissions": [{"accepted": True}]}, {"privateInputOverlap": True}), "inconclusive")

    def test_observed_action_counts_even_after_expiry(self):
        self.assertEqual(guarded_verdict({"newSubmissions": [{"accepted": True}]}, {"activeThroughout": False}), "bypass")

    def test_admitted_events_stop_the_input_gate_claim(self):
        self.assertEqual(guarded_verdict({"acceptedEvents": 1}, {"activeThroughout": True}), "admitted-input")

    def test_failed_active_window_cannot_establish_a_block(self):
        self.assertEqual(guarded_verdict({"verdict": "blocked"}, {"activeThroughout": False}), "inconclusive")

    def test_posting_error_cannot_establish_a_block(self):
        self.assertEqual(guarded_verdict({"verdict": "blocked", "attempt": {"postResults": [1]}}, {"activeThroughout": True}), "inconclusive")

    def test_verified_protected_refusal_counts(self):
        self.assertEqual(guarded_verdict({"verdict": "blocked", "attempt": {"postResults": [0]}}, {"activeThroughout": True}), "blocked")
