import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import calibrate_preview_compositor as calibration


class CalibrationTests(unittest.TestCase):
    def test_setup_wait_is_bounded_and_stop_wins_over_start(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "setup-complete").touch()
            (output / "stop").touch()
            self.assertFalse(calibration.await_setup(output, {"pid": 123}))
            (output / "stop").unlink()
            self.assertTrue(calibration.await_setup(output, {"pid": 123}))
            (output / "setup-complete").unlink()
            with patch.object(calibration.time, "monotonic", side_effect=[0, 61]):
                self.assertFalse(calibration.await_setup(output, {"pid": 123}))

    def test_missing_grant_starts_no_reference_or_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "artifacts").mkdir()
            output = root / "artifacts/calibration"
            with patch.object(calibration, "ROOT", root), patch.object(calibration, "matching_pids", return_value=set()), patch.object(calibration, "invoke", return_value={"screenRecordingGranted": False}), patch.object(calibration, "FixtureServer") as server, patch.object(calibration, "prepare") as prepare:
                report = calibration.calibrate(output)
            self.assertEqual(report["status"], "inconclusive")
            self.assertFalse(report["candidateLaunched"])
            server.assert_not_called()
            prepare.assert_not_called()
            self.assertEqual(json.loads((output / "results.json").read_text())["status"], "inconclusive")

    def test_failed_capture_still_closes_reference_and_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "artifacts").mkdir()
            output = root / "artifacts/calibration"
            worker = Mock()
            worker.is_alive.side_effect = [True, False]
            worker.ident = 1
            server = Mock(server_port=12345, controller_key="test-only")
            reference = {"pid": 123, "trial": {"id": "test"}}
            with patch.object(calibration, "ROOT", root), patch.object(calibration, "matching_pids", return_value=set()), patch.object(calibration, "invoke", return_value={"screenRecordingGranted": True}), patch.object(calibration, "FixtureServer", return_value=server), patch.object(calibration.threading, "Thread", return_value=worker), patch.object(calibration, "Oracle"), patch.object(calibration, "prepare", return_value=reference), patch.object(calibration, "capture", side_effect=RuntimeError("Failed test capture")), patch.object(calibration, "close") as close:
                report = calibration.calibrate(output)
            close.assert_called_once_with(reference)
            server.shutdown.assert_called_once()
            server.server_close.assert_called_once()
            worker.join.assert_called_once_with(timeout=3)
            self.assertTrue(report["referenceCleanupVerified"])
            self.assertTrue(report["fixtureStopped"])
            self.assertFalse(report["candidateLaunched"])
            self.assertEqual(report["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
