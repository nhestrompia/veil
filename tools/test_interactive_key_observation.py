import threading
import unittest

from run_interactive_key_observation import Controller, generated_reference, physical_reference_worked, reference_input_recorded


class InteractiveObservationTests(unittest.TestCase):
    def controller(self):
        controller = Controller.__new__(Controller)
        controller.lock = threading.RLock()
        controller.reference_accepted = 0
        controller.phase = "ready-reference"
        controller.worker = None
        return controller

    def test_typing_before_listener_ready_does_not_count(self):
        controller = self.controller()
        self.assertFalse(controller.accept_reference("native-input"))
        self.assertEqual(controller.reference_accepted, 0)

    def test_only_one_correct_submission_in_the_listening_interval_counts(self):
        controller = self.controller()
        controller.phase = "listening-reference"
        self.assertFalse(controller.accept_reference("wrong"))
        self.assertTrue(controller.accept_reference("native-input"))
        self.assertFalse(controller.accept_reference("native-input"))
        self.assertEqual(controller.reference_accepted, 1)

    def test_incomplete_reference_cannot_start_candidate(self):
        controller = self.controller()
        controller.phase = "ready-candidate"
        controller.report = {"samples": [{"newAcceptedSubmissions": 1}]}
        self.assertFalse(controller.start(True))

    def test_received_keys_without_matching_phrase_do_not_calibrate(self):
        row = {"inputGeneratedByController": False, "newAcceptedSubmissions": 1, "observerCleanupVerified": True,
               "observation": {"eventCount": 13, "monitorRemoved": True, "expectedFakePhraseMatched": False}}
        self.assertFalse(physical_reference_worked(row))

    def test_fixed_keycode_match_can_supply_the_reference(self):
        row = {"inputGeneratedByController": False, "newAcceptedSubmissions": 1, "observerCleanupVerified": True,
               "observation": {"eventCount": 13, "monitorRemoved": True,
                               "expectedFakePhraseMatched": False, "expectedFakeKeycodeSequenceMatched": True}}
        self.assertTrue(physical_reference_worked(row))

    def test_recorded_input_allows_exploration_without_becoming_decoder_calibration(self):
        row = {"inputGeneratedByController": False, "newAcceptedSubmissions": 1, "observerCleanupVerified": True,
               "observation": {"eventCount": 14, "monitorRemoved": True, "expectedFakePhraseMatched": False}}
        self.assertTrue(reference_input_recorded(row))
        self.assertFalse(physical_reference_worked(row))

    def test_generated_calibration_never_becomes_a_physical_reference(self):
        report = {"observerSHA256": "current", "physicalControl": False, "referencePID": 12345,
                  "acceptedSubmissions": 1, "observerCleanupVerified": True, "referenceCleanupVerified": True,
                  "observation": {"expectedFakePhraseMatched": True, "eventCount": 13, "monitorRemoved": True}}
        row = generated_reference(report, "current")
        self.assertTrue(reference_input_recorded(row))
        self.assertFalse(physical_reference_worked(row))
        with self.assertRaises(RuntimeError):
            generated_reference(report, "different")


if __name__ == "__main__":
    unittest.main()
