import unittest

from run_window_geometry import outcome


class GeometryOutcomeTests(unittest.TestCase):
    def test_action_counts_even_if_the_adapter_failed(self):
        self.assertEqual(outcome({"newAcceptedActions": 1, "attempted": False}, False), "autonomous-website-action")

    def test_private_overlap_cannot_establish_an_external_action(self):
        self.assertEqual(outcome({"newAcceptedActions": 1, "privateInputOverlap": True}, True), "inconclusive")

    def test_missing_positive_control_cannot_establish_a_block(self):
        self.assertEqual(outcome({"attempted": True, "refusedEvents": 20}, False), "inconclusive")

    def test_refused_window_gesture_has_a_narrow_result(self):
        self.assertEqual(outcome({"attempted": True, "refusedEvents": 20, "frameChanged": False}, True), "window-gesture-blocked")

    def test_changed_frame_without_action_is_a_separate_negative(self):
        self.assertEqual(outcome({"attempted": True, "frameChanged": True}, True), "no-page-action-observed")
