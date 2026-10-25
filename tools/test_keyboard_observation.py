import unittest

from run_keyboard_observation import worked


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


if __name__ == "__main__":
    unittest.main()
