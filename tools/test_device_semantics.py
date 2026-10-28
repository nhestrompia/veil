import copy
import unittest

from run_device_semantics import reference_worked


class SemanticControlTests(unittest.TestCase):
    def control(self):
        return {"readDisclosure": {"tree": True, "direct": True},
                "queries": {"tree": {"status": "observed"}, "direct": {"status": "observed"},
                            "menu": {"status": "observed", "items": [{"title": "Select All"}]},
                            "action": {"status": "attempted"}},
                "newSubmissions": [{"accepted": True}]}

    def test_each_read_route_needs_its_own_marker_control(self):
        row = self.control()
        self.assertTrue(reference_worked(row))
        for route in ["tree", "direct"]:
            failed = copy.deepcopy(row)
            failed["readDisclosure"][route] = False
            self.assertFalse(reference_worked(failed))

    def test_attempt_status_without_server_acceptance_is_not_a_control(self):
        row = self.control()
        row["newSubmissions"] = []
        self.assertFalse(reference_worked(row))

    def test_unreadable_menu_cannot_support_absence_claim(self):
        row = self.control()
        row["queries"]["menu"]["items"] = []
        self.assertFalse(reference_worked(row))


if __name__ == "__main__":
    unittest.main()
