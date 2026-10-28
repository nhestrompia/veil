import unittest

from native_environment import console_state, observe_console, action_verdict
from unittest.mock import patch
import plistlib


class ConsoleStateTests(unittest.TestCase):
    def test_locked_session_is_not_a_defensive_success(self):
        registry = {"IOConsoleUsers": [{"kCGSessionLoginDoneKey": True, "CGSSessionScreenIsLocked": True}]}
        self.assertIs(console_state(registry)["locked"], True)

    def test_unlocked_console(self):
        registry = [{"IOConsoleUsers": [{"kCGSessionLoginDoneKey": True, "CGSSessionScreenIsLocked": False}]}]
        self.assertIs(console_state(registry)["locked"], False)

    def test_missing_or_ambiguous_state_is_unknown(self):
        for sessions in [[], [{"kCGSessionLoginDoneKey": True}],
                         [{"kCGSessionLoginDoneKey": True}, {"kCGSessionLoginDoneKey": True}]]:
            with self.subTest(sessions=sessions):
                self.assertIsNone(console_state({"IOConsoleUsers": sessions})["locked"])

    def test_lock_flag_does_not_veto_a_working_attack_route(self):
        registry = {"IOConsoleUsers": [{"kCGSessionLoginDoneKey": True, "CGSSessionScreenIsLocked": True}]}
        with patch("native_environment.subprocess.check_output", return_value=plistlib.dumps(registry)):
            self.assertEqual(observe_console(), {"locked": True, "advisory": True})
        self.assertEqual(action_verdict(True, False, False), "bypass")

    def test_refusal_without_a_working_control_is_inconclusive(self):
        self.assertEqual(action_verdict(False, True, False), "inconclusive")
        self.assertEqual(action_verdict(False, True, True), "blocked")
        self.assertEqual(action_verdict(False, False, True), "inconclusive")


if __name__ == "__main__":
    unittest.main()
