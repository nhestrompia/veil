import unittest

from run_focus_attack import cycle_outcome


class FocusAttackTests(unittest.TestCase):
    def test_failed_activation_is_not_a_block(self):
        self.assertEqual(cycle_outcome({"newSubmissions": [], "awayStatus": "inconclusive", "backStatus": "observed"}), "inconclusive")

    def test_action_remains_a_bypass_despite_failed_activation_receipt(self):
        self.assertEqual(cycle_outcome({"newSubmissions": [{"accepted": True}], "awayStatus": "inconclusive", "backStatus": "inconclusive"}), "autonomous-website-action")
