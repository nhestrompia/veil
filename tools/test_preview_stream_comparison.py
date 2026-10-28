import unittest
from pathlib import Path
from unittest.mock import patch

import run_preview_stream_comparison as comparison
from run_preview_stream_comparison import fully_audited, score


def audited(marker=False, colored=0):
    return {"status": "audited", "streamStopped": True, "cleanupVerified": True,
            "durationSeconds": 30, "elapsedSeconds": 30.5, "completeFrames": 10,
            "auditedFrames": 10, "nonBlackFrames": colored, "markerRecovered": marker}


class StreamComparisonTests(unittest.TestCase):
    def test_readonly_metadata_probes_launch_in_background(self):
        replies = [{"status": "observed"}, {"windows": [{"kCGWindowOwnerPID": 123, "kCGWindowLayer": 0, "kCGWindowNumber": 456}]}]
        with patch.object(comparison, "probe", side_effect=replies) as probe, patch.object(comparison, "invoke", return_value={"status": "inconclusive"}):
            comparison.capture({"pid": 123}, "window", Path("/unused"), None)
        self.assertEqual(probe.call_count, 2)
        self.assertTrue(all(call.kwargs.get("background") is True for call in probe.call_args_list))

    def test_unapproved_capture_never_launches(self):
        with patch.object(comparison, "verified_manifest", return_value=({"permissionApproved": False}, Path("/unused"))), patch.object(comparison.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(RuntimeError, "needs approval"):
                comparison.invoke(["window", 123, 456], Path("/unused.json"))
            launch.assert_not_called()

    def test_runner_cannot_request_a_permission(self):
        with patch.object(comparison, "verified_manifest", return_value=({"permissionApproved": True}, Path("/unused"))), patch.object(comparison.subprocess, "Popen") as launch:
            with self.assertRaises(ValueError):
                comparison.invoke(["request-screen-recording"], Path("/unused.json"))
            launch.assert_not_called()

    def test_valid_complete_black_stream_with_matched_controls(self):
        self.assertEqual(score(audited(True, 10), audited(), audited(True, 10)),
                         "all-delivered-complete-frames-black")

    def test_missing_frames_are_inconclusive(self):
        row = audited()
        row.update(completeFrames=0, auditedFrames=0)
        self.assertFalse(fully_audited(row))

    def test_partially_audited_frames_are_inconclusive(self):
        row = audited()
        row["auditedFrames"] = 9
        self.assertEqual(score(audited(True, 10), row, audited(True, 10)), "inconclusive")

    def test_short_duration_does_not_pass_steady_stream(self):
        for key, value in [("durationSeconds", 2), ("elapsedSeconds", 2)]:
            row = audited()
            row[key] = value
            with self.subTest(key=key):
                self.assertFalse(fully_audited(row))

    def test_failed_reference_cannot_establish_blocking(self):
        self.assertEqual(score(audited(), audited(), audited(True, 10)), "inconclusive")
        self.assertEqual(score(audited(True, 10), audited(), audited()), "inconclusive")

    def test_nonblack_output_without_marker_is_not_black_result(self):
        self.assertEqual(score(audited(True, 10), audited(False, 1), audited(True, 10)),
                         "nonblack-output-marker-not-recovered")

    def test_marker_disclosure_is_a_bypass(self):
        self.assertEqual(score(audited(True, 10), audited(True, 1), audited(True, 10)), "marker-recovered")

    def test_cleanup_or_stop_failure_is_inconclusive(self):
        for key in ["streamStopped", "cleanupVerified"]:
            row = audited()
            row[key] = False
            with self.subTest(key=key):
                self.assertFalse(fully_audited(row))
