import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_loaded_page_attacks as loaded


class LoadedPageTests(unittest.TestCase):
    def test_private_startup_action_is_not_an_external_success(self):
        before = {"submissions": [{"accepted": True}], "events": []}
        after = {"submissions": [{"accepted": True}], "events": []}
        result = loaded.score_after_attempt(before, after, "INPUT_GATE_REFUSED type=10\n", True, True)
        self.assertEqual(result["verdict"], "blocked")
        self.assertEqual(result["newSubmissions"], [])

    def test_new_action_wins_even_when_the_tool_fails(self):
        before = {"submissions": [{"accepted": True}], "events": []}
        after = {"submissions": [{"accepted": True}, {"accepted": True}], "events": []}
        result = loaded.score_after_attempt(before, after, "", False, True)
        self.assertEqual(result["verdict"], "bypass")

    def test_missing_reference_or_refusal_cannot_pass(self):
        state = {"submissions": [], "events": []}
        for refused, attempted, control in [("", True, True), ("INPUT_GATE_REFUSED", False, True),
                                            ("INPUT_GATE_REFUSED", True, False)]:
            self.assertEqual(loaded.score_after_attempt(state, state, refused, attempted, control)["verdict"], "inconclusive")

    def test_geometry_only_translates_matching_windows(self):
        control = {"windowFrame": [100, 200, 1000, 740], "fieldCenter": [500, 500]}
        self.assertEqual(loaded.translated_point(control, [200, 100, 1000, 740]), [600, 400])
        with self.assertRaises(RuntimeError):
            loaded.translated_point(control, [200, 100, 900, 740])

    def test_pid_delivery_modes_remain_distinct(self):
        self.assertEqual(loaded.arguments_for("pid-hid", 12345, [10, 20]),
                         ["input", 12345, 10, 20, "hid", "pid"])
        self.assertEqual(loaded.arguments_for("pid-window-keycodes-hid", 12345, [10, 20]),
                         ["input", 12345, 10, 20, "hid", "pid-window", "keycodes"])

    def test_failed_reference_does_not_prepare_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = {"pid": 12345}
            permission = {"accessibility": True, "postEvents": True, "screenCapture": True,
                          "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            row = {"verdict": "inconclusive", "route": "hid"}
            with patch.object(loaded, "probe", return_value=permission), patch.object(loaded, "observe_console", return_value={}), patch.object(loaded, "Oracle"), patch.object(loaded, "prepare", return_value=session) as prepare, patch.object(loaded, "attack", return_value=row), patch.object(loaded, "close"), contextlib.redirect_stdout(io.StringIO()):
                report = loaded.run(root, 1, ["hid"], "hid")
            prepare.assert_called_once()
            self.assertEqual(prepare.call_args.args[0], "InspectableControl")
            self.assertEqual(report["cleanup"], [{"pid": 12345, "verified": True}])

    def test_cleanup_failure_is_saved_and_stops_the_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            permission = {"accessibility": True, "postEvents": True, "screenCapture": True,
                          "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            with patch.object(loaded, "probe", return_value=permission), patch.object(loaded, "observe_console", return_value={}), patch.object(loaded, "Oracle"), patch.object(loaded, "prepare", return_value={"pid": 12345}), patch.object(loaded, "attack", return_value={"verdict": "bypass"}), patch.object(loaded, "close", side_effect=RuntimeError("cleanup failed")), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                loaded.run(root, 1, ["hid"], "hid")
            report = json.loads((root / "results.json").read_text())
            self.assertEqual(report["cleanup"], [{"pid": 12345, "verified": False}])

    def test_unavailable_field_stops_other_routes_and_repetitions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            permission = {"accessibility": True, "postEvents": True, "screenCapture": True,
                          "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            row = {"verdict": "inconclusive", "referenceFieldUnavailable": True}
            with patch.object(loaded, "probe", return_value=permission), patch.object(loaded, "observe_console", return_value={}), patch.object(loaded, "Oracle"), patch.object(loaded, "prepare", return_value={"pid": 12345}) as prepare, patch.object(loaded, "attack", return_value=row) as attack, patch.object(loaded, "close"), contextlib.redirect_stdout(io.StringIO()):
                report = loaded.run(root, 3, ["hid", "session"], "session")
            prepare.assert_called_once()
            attack.assert_called_once()
            self.assertTrue(report["stoppedEarly"])
            self.assertEqual(report["cleanup"], [{"pid": 12345, "verified": True}])
            self.assertTrue(json.loads((root / "results.json").read_text())["stoppedEarly"])


if __name__ == "__main__":
    unittest.main()
