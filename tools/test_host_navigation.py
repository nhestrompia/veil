import unittest

from run_host_navigation import reload_worked


class HostNavigationTests(unittest.TestCase):
    def control(self):
        return {"newPageReadyEvents": 1, "newAcceptedFormActions": 0,
                "observation": {"status": "observed", "accessibilityQueried": True,
                                "cleanupVerified": True, "queries": [
                    {"processKind": "host", "navigationContextVerified": True,
                     "reloadActionAttempted": True, "reloadPressError": 0}]}}

    def test_press_without_navigation_does_not_count(self):
        row = self.control()
        self.assertTrue(reload_worked(row))
        row["newPageReadyEvents"] = 0
        self.assertFalse(reload_worked(row))

    def test_lifecycle_event_without_verified_action_does_not_count(self):
        for key in ["navigationContextVerified", "reloadActionAttempted"]:
            row = self.control()
            row["observation"]["queries"][0][key] = False
            self.assertFalse(reload_worked(row))

    def test_extra_form_action_does_not_count_as_reload_only(self):
        row = self.control()
        row["newAcceptedFormActions"] = 1
        self.assertFalse(reload_worked(row))

    def test_unavailable_observation_does_not_count(self):
        row = self.control()
        row["observation"]["status"] = "inconclusive"
        self.assertFalse(reload_worked(row))
