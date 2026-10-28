import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import run_preview_compositor_comparison as comparison


def audited(reference=False):
    return {"status": "audited", "streamStopped": True, "cleanupVerified": True, "backdropClosed": True,
            "completeFrames": 30, "auditedFrames": 30, "nonuniformFrames": 30 if reference else 0,
            "markerRecovered": reference, "stageMarkers": [reference] * 3,
            "stages": [{"filter": name, "completeFrames": 10, "auditedFrames": 10, "elapsedSeconds": 3.1}
                       for name in ["unfiltered-display", "owned-apps", "unfiltered-display"]]}


class CompositorComparisonTests(unittest.TestCase):
    def test_uniform_stream_requires_readable_controls_in_every_stage(self):
        reference = audited(True)
        self.assertEqual(comparison.score(reference, audited(), reference),
                         "all-delivered-complete-frames-spatially-uniform")
        for stage in range(3):
            failed = copy.deepcopy(reference)
            failed["stageMarkers"][stage] = False
            self.assertEqual(comparison.score(failed, audited(), reference), "inconclusive")

    def test_missing_or_unaudited_frames_never_pass(self):
        for key, value in [("completeFrames", 0), ("auditedFrames", 29), ("backdropClosed", False),
                           ("cleanupVerified", False), ("streamStopped", False)]:
            row = audited()
            row[key] = value
            with self.subTest(key=key):
                self.assertFalse(comparison.fully_audited(row))
        for stage in range(3):
            row = audited()
            row["stages"][stage]["completeFrames"] = 0
            self.assertFalse(comparison.fully_audited(row))

    def test_filter_order_and_duration_matter(self):
        for key, value in [("filter", "unfiltered-display"), ("elapsedSeconds", 2)]:
            row = audited()
            row["stages"][1][key] = value
            self.assertFalse(comparison.fully_audited(row))

    def test_nonuniform_pixels_are_never_a_uniform_result(self):
        row = audited()
        row["nonuniformFrames"] = 1
        self.assertEqual(comparison.score(audited(True), row, audited(True)), "nonuniform-output-marker-not-recovered")
        row["markerRecovered"] = True
        self.assertEqual(comparison.score(audited(True), row, audited(True)), "marker-recovered")

    def test_no_unapproved_stream_or_implicit_request(self):
        with patch.object(comparison, "verified_manifest", return_value=({"permissionApproved": False}, Path("/unused"))), patch.object(comparison.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(RuntimeError, "needs approval"):
                comparison.invoke(["sequence", 123, 456], Path("/unused.json"))
            with self.assertRaises(ValueError):
                comparison.invoke(["request-screen-recording"], Path("/unused.json"))
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
