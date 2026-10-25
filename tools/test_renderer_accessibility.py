import unittest

from run_renderer_accessibility import read_reference_worked, reference_worked


class RendererCalibrationTests(unittest.TestCase):
    def control(self):
        return {"markerRecovered": True, "acceptedActions": 1,
                "observation": {"status": "observed", "accessibilityQueried": True, "cleanupVerified": True,
                                "queries": [{"actionAttempted": True, "fixtureURLVerified": True,
                                             "setValueError": 0, "pressError": 0}]}}

    def test_readable_marker_without_action_does_not_calibrate(self):
        row = self.control()
        self.assertTrue(reference_worked(row))
        row["acceptedActions"] = 0
        self.assertFalse(reference_worked(row))
        self.assertTrue(read_reference_worked(row))

    def test_attempt_without_fixture_verification_does_not_calibrate(self):
        row = self.control()
        row["observation"]["queries"][0]["fixtureURLVerified"] = False
        self.assertFalse(reference_worked(row))

    def test_action_without_disclosure_does_not_calibrate_read_route(self):
        row = self.control()
        row["markerRecovered"] = False
        self.assertFalse(reference_worked(row))

    def test_missing_query_or_cleanup_does_not_calibrate(self):
        for key in ["accessibilityQueried", "cleanupVerified"]:
            row = self.control()
            row["observation"][key] = False
            self.assertFalse(reference_worked(row))


if __name__ == "__main__":
    unittest.main()
