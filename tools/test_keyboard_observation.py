import unittest
from pathlib import Path
import tempfile

from run_keyboard_observation import wait_for_observer_ready, worked


class ObserverControlTests(unittest.TestCase):
    def control(self):
        return {"acceptedSubmissions": 1, "observation": {"expectedFakePhraseMatched": True,
                "eventCount": 12, "monitorRemoved": True}, "observerCleanupVerified": True,
                "referenceCleanupVerified": True}

    def test_received_events_without_fake_phrase_are_not_calibration(self):
        row = self.control()
        self.assertTrue(worked(row))
        row["observation"]["expectedFakePhraseMatched"] = False
        self.assertFalse(worked(row))

    def test_read_phrase_without_task_completion_is_not_calibration(self):
        row = self.control()
        row["acceptedSubmissions"] = 0
        self.assertFalse(worked(row))

    def test_cleanup_must_finish_before_control_counts(self):
        row = self.control()
        row["observerCleanupVerified"] = False
        self.assertFalse(worked(row))

    def test_fixed_keycode_match_can_calibrate_without_unicode(self):
        row = self.control()
        row["observation"]["expectedFakePhraseMatched"] = False
        row["observation"]["expectedFakeKeycodeSequenceMatched"] = True
        self.assertTrue(worked(row))

    def test_running_process_is_not_a_readiness_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "stderr").write_text("")
            with self.assertRaises(RuntimeError):
                wait_for_observer_ready(root / "stderr", root / "stdout", timeout=0)

    def test_armed_run_loop_marker_is_a_readiness_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "stderr").write_text("OBSERVER_ARMED\n")
            wait_for_observer_ready(root / "stderr", root / "stdout")

    def test_ended_observer_is_not_ready_even_with_an_earlier_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "stderr").write_text("OBSERVER_ARMED\n")
            (root / "stdout").write_text('{"status":"inconclusive"}')
            with self.assertRaises(RuntimeError):
                wait_for_observer_ready(root / "stderr", root / "stdout")


if __name__ == "__main__":
    unittest.main()
