import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_device_capture as capture


class DeviceCaptureTests(unittest.TestCase):
    def test_failed_capture_remains_inconclusive_without_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(capture, "probe", return_value={"status": "inconclusive"}) as probe:
                row = capture.capture(12345, {}, "system-capture", Path(directory) / "sample", Mock())
            self.assertEqual(row["observation"], "inconclusive")
            probe.assert_called_once()

    def run_control(self, directory, *, recovered=False, close_error=None):
        root = Path(directory)
        binary = root / "probe"
        binary.parent.mkdir(exist_ok=True)
        binary.write_bytes(b"probe")
        session = root / "session.json"
        log = root / "session.log"
        log.write_text("DEVICE_KEYBOARD bound=true\n")
        session.write_text(json.dumps({"pid": 12345, "trial": {}, "log": str(log), "binarySHA256": "frozen"}))
        oracle = Mock()
        oracle.state.return_value = {"submissions": [{"accepted": True}]}
        reference = {"pid": 67890, "trial": {}, "binarySHA256": "reference"}
        row = {"observation": "marker-not-recovered", "markerRecovered": recovered,
               "capture": {"probeBinarySHA256": capture.hashlib.sha256(b"probe").hexdigest()}}
        with patch.object(capture, "ROOT", root), patch.object(capture, "active"), patch.object(capture, "Oracle", return_value=oracle), patch.object(capture, "probe", return_value={"screenCapture": True}), patch.object(capture, "prepare", return_value=reference), patch.object(capture, "close", side_effect=close_error), patch.object(capture, "capture", return_value=row) as attempt:
            with patch.object(Path, "read_bytes", return_value=b"probe"):
                if close_error:
                    with self.assertRaisesRegex(RuntimeError, "cleanup"):
                        capture.run(session, root / "out", 1, True, ["capture"])
                else:
                    capture.run(session, root / "out", 1, True, ["capture"])
        return attempt, json.loads((root / "out/results.json").read_text())

    def test_no_marker_in_reference_skips_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt, report = self.run_control(directory)
            attempt.assert_called_once()
            self.assertTrue(report["results"][0]["skipped"])
            self.assertTrue(report["controls"][0]["cleanupVerified"])

    def test_cleanup_failure_stops_before_candidate_and_saves(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt, report = self.run_control(directory, recovered=True, close_error=RuntimeError("cleanup failed"))
            attempt.assert_called_once()
            self.assertEqual(report["results"], [])
            self.assertFalse(report["controls"][0]["cleanupVerified"])


if __name__ == "__main__":
    unittest.main()
