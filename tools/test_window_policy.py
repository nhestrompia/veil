import unittest

from run_window_policy import result


class WindowPolicyOutcomeTests(unittest.TestCase):
    def test_new_action_cannot_be_hidden_by_a_failed_tool(self):
        self.assertEqual(result({"newAcceptedActions": 1}, False), "geometry-triggered-action")

    def test_no_attempt_or_no_reference_is_inconclusive(self):
        row = {"policyRefusals": 1, "frameChanged": False}
        self.assertEqual(result(row, True), "inconclusive")
        row["attempted"] = True
        self.assertEqual(result(row, False), "inconclusive")

    def test_frame_change_or_missing_policy_receipt_cannot_establish_refusal(self):
        row = {"attempted": True, "policyRefusals": 1, "frameChanged": True}
        self.assertEqual(result(row, True), "inconclusive")
        row.update(frameChanged=False, policyRefusals=0)
        self.assertEqual(result(row, True), "inconclusive")

    def test_calibrated_policy_refusal_has_a_narrow_result(self):
        row = {"attempted": True, "policyRefusals": 1, "frameChanged": False}
        self.assertEqual(result(row, True), "native-zoom-refused")
