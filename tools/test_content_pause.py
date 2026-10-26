import unittest

from research_content_pause import pause_outcome


class ContentPauseTests(unittest.TestCase):
    def test_unverified_pause_cannot_prove_an_action(self):
        self.assertEqual(pause_outcome({"interventionVerified": False, "newSubmissions": [{"accepted": True}]}), "inconclusive")

    def test_overlapping_private_input_is_inconclusive(self):
        self.assertEqual(pause_outcome({"interventionVerified": True, "acceptedInputEvents": 1,
                                      "newSubmissions": [{"accepted": True}]}), "inconclusive")

    def test_verified_action_is_a_bypass(self):
        self.assertEqual(pause_outcome({"interventionVerified": True, "acceptedInputEvents": 0,
                                      "newSubmissions": [{"accepted": True}]}), "autonomous-website-action")

    def test_verified_pause_without_action_is_bounded_negative(self):
        self.assertEqual(pause_outcome({"interventionVerified": True, "acceptedInputEvents": 0,
                                      "newSubmissions": []}), "no-action-observed")
