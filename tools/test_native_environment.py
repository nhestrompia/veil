import unittest

from native_environment import console_state


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


if __name__ == "__main__":
    unittest.main()
