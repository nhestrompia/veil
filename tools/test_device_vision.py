import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_device_vision as vision


class DeviceVisionTests(unittest.TestCase):
    def files(self, root):
        log = root / "session.log"
        log.write_text("DEVICE_KEYBOARD bound=true\n")
        session = root / "session.json"
        session.write_text(json.dumps({"pid": 12345, "trial": {"id": "local"}, "log": str(log),
                                      "binarySHA256": "candidate"}))
        binary = root / "control-binary"
        binary.write_bytes(b"control")
        oracle = Mock()
        oracle.state.return_value = {"submissions": [{"accepted": True}]}
        oracle.create.return_value = {"id": "reference", "url": "http://127.0.0.1/reference"}
        permission = {"postEvents": True, "screenCapture": True,
                      "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
        return session, binary, oracle, permission

    def test_relative_capture_argument_is_absolute(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "reference.log"
            log.write_text("")
            oracle = Mock()
            oracle.state.return_value = {"submissions": [], "secret": "fake"}
            with patch.object(vision, "probe", return_value={"status": "inconclusive"}) as probe:
                vision.attempt(12345, {"id": "local"}, Path("relative-output") / "sample", oracle, log)
            self.assertTrue(probe.call_args.args[0][2].is_absolute())
            self.assertTrue(probe.call_args.args[1].is_absolute())

    def test_failed_control_never_attempts_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, binary, oracle, permission = self.files(root)
            launcher = Mock()
            with patch.object(vision, "active"), patch.object(vision, "Oracle", return_value=oracle), patch.object(vision, "probe", return_value=permission), patch.object(vision, "launch", return_value=(launcher, binary)), patch.object(vision, "ready", return_value=67890), patch.object(vision, "attempt", return_value={"verdict": "inconclusive"}) as attempt, patch.object(vision, "stop_launched", return_value=True), patch.object(vision.time, "sleep"):
                vision.run(session, root / "out", 1, True)
            attempt.assert_called_once()
            self.assertEqual(attempt.call_args.args[0], 67890)
            report = json.loads((root / "out/results.json").read_text())
            self.assertTrue(report["results"][0]["skipped"])
            self.assertTrue(report["controls"][0]["cleanupVerified"])

    def test_black_image_falls_back_to_matched_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "reference.log"
            log.write_text("")
            oracle = Mock()
            oracle.state.return_value = {"submissions": [], "secret": "fake"}
            reference = {"capture": {"frame": [10, 20, 1000, 772]}, "fieldCenter": [510, 420]}
            replies = [{"status": "captured", "frame": [100, 110, 1000, 772]}, {"text": []}, {"status": "attempted"}]
            with patch.object(vision, "probe", side_effect=replies) as probe, patch.object(vision.time, "sleep"):
                row = vision.attempt(12345, {"id": "local"}, root / "candidate", oracle, log, reference)
            self.assertEqual(probe.call_args.args[0], ["input", 12345, 600, 510, "hid", "curve"])
            self.assertEqual(row["coordinateSource"], "Matched reference geometry after target OCR failed")

    def test_geometry_change_prevents_blind_fallback_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "reference.log"
            log.write_text("")
            oracle = Mock()
            oracle.state.return_value = {"submissions": [], "secret": "fake"}
            reference = {"capture": {"frame": [10, 20, 1000, 772]}, "fieldCenter": [510, 420]}
            with patch.object(vision, "probe", side_effect=[{"status": "captured", "frame": [100, 110, 900, 772]}, {"text": []}]) as probe:
                row = vision.attempt(12345, {"id": "local"}, root / "candidate", oracle, log, reference)
            self.assertEqual(probe.call_count, 2)
            self.assertEqual(row["verdict"], "inconclusive")
            self.assertIn("sizes differ", row["error"])

    def test_failed_readiness_cleans_the_launch_and_saves_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, binary, oracle, permission = self.files(root)
            launcher = Mock()
            with patch.object(vision, "active"), patch.object(vision, "Oracle", return_value=oracle), patch.object(vision, "probe", return_value=permission), patch.object(vision, "launch", return_value=(launcher, binary)), patch.object(vision, "ready", side_effect=RuntimeError("not ready")), patch.object(vision, "attempt") as attempt, patch.object(vision, "stop_launched", return_value=True) as stop:
                vision.run(session, root / "out", 1, True)
            stop.assert_called_once_with(launcher, binary, None)
            attempt.assert_not_called()
            report = json.loads((root / "out/results.json").read_text())
            self.assertEqual(report["controls"][0]["error"], "not ready")
            self.assertTrue(report["results"][0]["skipped"])

    def test_cleanup_failure_stops_before_candidate_and_is_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, binary, oracle, permission = self.files(root)
            with patch.object(vision, "active"), patch.object(vision, "Oracle", return_value=oracle), patch.object(vision, "probe", return_value=permission), patch.object(vision, "launch", return_value=(Mock(), binary)), patch.object(vision, "ready", return_value=67890), patch.object(vision, "attempt", return_value={"verdict": "bypass"}) as attempt, patch.object(vision, "stop_launched", return_value=False), patch.object(vision.time, "sleep"), self.assertRaisesRegex(RuntimeError, "cleanup failed"):
                vision.run(session, root / "out", 1, True)
            attempt.assert_called_once()
            report = json.loads((root / "out/results.json").read_text())
            self.assertFalse(report["controls"][0]["cleanupVerified"])
            self.assertEqual(report["results"], [])


if __name__ == "__main__":
    unittest.main()
