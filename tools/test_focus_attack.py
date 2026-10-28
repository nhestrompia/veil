import unittest

from run_focus_attack import cycle_outcome


class FocusAttackTests(unittest.TestCase):
    def test_failed_activation_is_not_a_block(self):
        self.assertEqual(cycle_outcome({"newSubmissions": [], "awayStatus": "inconclusive", "backStatus": "observed"}), "inconclusive")

    def test_action_remains_a_bypass_despite_failed_activation_receipt(self):
        self.assertEqual(cycle_outcome({"newSubmissions": [{"accepted": True}], "awayStatus": "inconclusive", "backStatus": "inconclusive"}), "autonomous-website-action")

    def test_private_input_overlap_cannot_establish_an_autonomous_action(self):
        cycle = {"acceptedInputEvents": 1, "newSubmissions": [{"accepted": True}], "awayStatus": "observed", "backStatus": "observed"}
        self.assertEqual(cycle_outcome(cycle), "inconclusive")

    def test_zero_input_action_remains_a_bypass(self):
        cycle = {"acceptedInputEvents": 0, "newSubmissions": [{"accepted": True}], "awayStatus": "inconclusive", "backStatus": "inconclusive"}
        self.assertEqual(cycle_outcome(cycle), "autonomous-website-action")

    def test_private_input_overlap_cannot_establish_a_block(self):
        cycle = {"acceptedInputEvents": 1, "newSubmissions": [], "awayStatus": "observed", "backStatus": "observed"}
        self.assertEqual(cycle_outcome(cycle), "inconclusive")
