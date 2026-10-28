import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_preview_renderer_token_comparison as comparison


def observation(markers, incomplete=False):
    return {"status": "observed", "accessibilityQueried": True, "cleanupVerified": True,
            "queries": [{"kind": "renderer", "researchMarkers": markers, "traversalIncomplete": incomplete}]}


class TokenComparisonTests(unittest.TestCase):
    def exercise(self, root, control, candidate=None, activation="observed", cleanup_error=None):
        log = root / "browser.log"
        log.write_text("DEVICE_KEYBOARD bound=true")
        session = root / "session.json"
        session.write_text(json.dumps({"pid": 123, "binarySHA256": "pinned", "log": str(log),
                                       "controller": "private", "trial": {"id": "candidate"}}))
        physical = root / "physical.json"
        physical.write_text(json.dumps({"operatorDeclaresPhysicalCompletion": True, "pid": 123,
                                        "binarySHA256": "pinned", "deviceBound": True, "acceptedSubmissions": 1}))
        oracle = Mock()
        oracle.state.side_effect = lambda trial: {"secret": "AFB-0123ABCD", "submissions":
                                                   [{"accepted": True}] if trial["id"] == "candidate" else []}
        (root / "artifacts").mkdir()
        replies = [{"accessibility": True}, control] + ([candidate] if candidate is not None else [])
        with patch.object(comparison, "ROOT", root), patch.object(comparison, "active"), patch.object(comparison, "verified_helper", return_value="reviewed"), patch.object(comparison, "matching_pids", return_value=set()), patch.object(comparison, "Oracle", return_value=oracle), patch.object(comparison, "prepare", return_value={"pid": 456, "trial": {"id": "reference"}}), patch.object(comparison, "probe", side_effect=[{"status": "observed"}, {"status": activation}]), patch.object(comparison, "observe", side_effect=replies) as observe, patch.object(comparison, "close", side_effect=cleanup_error) as close:
            if cleanup_error:
                with self.assertRaisesRegex(RuntimeError, "cleanup"):
                    comparison.run(session, physical, root / "artifacts/result")
            else:
                comparison.run(session, physical, root / "artifacts/result")
        return json.loads((root / "artifacts/result/results.json").read_text()), observe.call_count, close.call_count

    def test_failed_reference_skips_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            report, calls, closes = self.exercise(Path(directory), observation([]))
            self.assertFalse(report["candidateQueried"])
            self.assertEqual((calls, closes), (2, 1))

    def test_incomplete_scan_cannot_be_a_negative_result(self):
        with tempfile.TemporaryDirectory() as directory:
            report, _, _ = self.exercise(Path(directory), observation(["AFB-0123ABCD"]), observation([], True))
            self.assertEqual(report["readOutcome"], "inconclusive")

    def test_recovered_candidate_marker_is_a_read_bypass(self):
        with tempfile.TemporaryDirectory() as directory:
            report, _, _ = self.exercise(Path(directory), observation(["AFB-0123ABCD"]), observation(["AFB-0123ABCD"]))
            self.assertEqual(report["readOutcome"], "renderer-marker-recovered")

    def test_failed_candidate_activation_sends_no_query(self):
        with tempfile.TemporaryDirectory() as directory:
            report, calls, _ = self.exercise(Path(directory), observation(["AFB-0123ABCD"]), activation="refused")
            self.assertFalse(report["candidateQueried"])
            self.assertEqual(calls, 2)

    def test_reference_cleanup_failure_stops_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            report, calls, _ = self.exercise(Path(directory), observation(["AFB-0123ABCD"]), cleanup_error=RuntimeError("cleanup failed"))
            self.assertFalse(report["candidateQueried"])
            self.assertEqual(calls, 2)
