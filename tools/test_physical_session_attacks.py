import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_physical_session_attacks as physical


class PhysicalSessionAttackTests(unittest.TestCase):
    def run_rows(self, root, rows, close_error=None):
        binary = root / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"frozen")
        log = root / "browser.log"
        log.write_text("DEVICE_KEYBOARD bound=true")
        session = root / "session.json"
        session.write_text(json.dumps({"pid": 12345, "trial": {"id": "local"},
                                       "log": str(log), "binarySHA256": "browser"}))
        oracle = Mock()
        oracle.state.return_value = {"submissions": [{"accepted": True}]}
        permissions = {"accessibility": True, "postEvents": True, "status": "observed",
                       "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
        with patch.object(physical, "ROOT", root), patch.object(physical, "active"), patch.object(physical, "matching_pids", return_value=set()), patch.object(physical, "Oracle", return_value=oracle), patch.object(physical, "probe", return_value=permissions), patch.object(physical, "prepare", return_value={"pid": 67890}), patch.object(physical, "close", side_effect=close_error), patch.object(physical, "attack", side_effect=rows) as attack, contextlib.redirect_stdout(io.StringIO()):
            if close_error:
                with self.assertRaisesRegex(RuntimeError, "cleanup"):
                    physical.run(session, root / "results", ["hid"], 1)
            else:
                physical.run(session, root / "results", ["hid"], 1)
        return attack.call_count, json.loads((root / "results/results.json").read_text())

    def test_failed_reference_skips_physical_session(self):
        with tempfile.TemporaryDirectory() as directory:
            count, report = self.run_rows(Path(directory), [{"verdict": "inconclusive"}])
            self.assertEqual(count, 1)
            self.assertTrue(report["results"][0]["skipped"])

    def test_accepted_partial_input_stops_following_trials(self):
        with tempfile.TemporaryDirectory() as directory:
            count, report = self.run_rows(Path(directory), [
                {"verdict": "bypass"}, {"verdict": "inconclusive", "acceptedEvents": 1}])
            self.assertEqual(count, 2)
            self.assertTrue(report["stoppedEarly"])

    def test_posting_error_prevents_block_verdict(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report = self.run_rows(Path(directory), [
                {"verdict": "bypass"}, {"verdict": "blocked", "attempt": {"postResults": [1]}}])
            self.assertEqual(report["results"][0]["verdict"], "inconclusive")

    def test_reference_cleanup_failure_stops_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            count, report = self.run_rows(Path(directory), [{"verdict": "bypass"}], RuntimeError("cleanup failed"))
            self.assertEqual(count, 1)
            self.assertEqual(report["results"], [])

    def test_missing_candidate_geometry_stops_following_trials(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report = self.run_rows(Path(directory), [
                {"verdict": "bypass"}, {"verdict": "inconclusive", "error": "No owned normal research window"}])
            self.assertTrue(report["stoppedEarly"])
