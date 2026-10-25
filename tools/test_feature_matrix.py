import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_feature_matrix as matrix


class FeatureMatrixTests(unittest.TestCase):
    def test_action_during_failed_reference_preparation_still_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["InternalKeyboardControl", "InspectableControl", "NativeProbe"]:
                binary = root / f"dist/{name}.app/Contents/MacOS/{name}"
                binary.parent.mkdir(parents=True)
                binary.write_bytes(b"frozen")
            log = root / "candidate.log"
            log.write_text("focusAssistedByDiagnostic=true")
            oracle = Mock()
            oracle.state.side_effect = [{"submissions": [{"accepted": True}]},
                                        {"submissions": [{"accepted": True}, {"accepted": True}]}]
            permissions = {"accessibility": True, "postEvents": True, "screenCapture": True,
                           "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            candidate = {"pid": 12345, "log": log, "trial": {"id": "local"}}
            with patch.object(matrix, "ROOT", root), patch.object(matrix, "Oracle", return_value=oracle), patch.object(matrix, "probe", return_value=permissions), patch.object(matrix, "matching_pids", return_value=set()), patch.object(matrix, "prepare", side_effect=[candidate, {"pid": 67890}]), patch.object(matrix, "close"), patch.object(matrix, "attack", return_value={"verdict": "inconclusive"}) as attack, contextlib.redirect_stdout(io.StringIO()):
                report = matrix.run(root / "output", root / "controller.json", ["focus-action"], ["hid"])
            attack.assert_called_once()
            result = report["surfaces"][0]["results"][0]
            self.assertEqual(result["verdict"], "bypass")
            self.assertEqual(result["operationPhase"], "reference-focus-transition")
            self.assertFalse(result["syntheticInputPosted"])

    def test_failed_internal_task_prevents_external_attacks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["InternalKeyboardControl", "InspectableControl", "NativeProbe"]:
                binary = root / f"dist/{name}.app/Contents/MacOS/{name}"
                binary.parent.mkdir(parents=True)
                binary.write_bytes(b"frozen")
            permissions = {"accessibility": True, "postEvents": True, "screenCapture": True,
                           "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            with patch.object(matrix, "ROOT", root), patch.object(matrix, "Oracle"), patch.object(matrix, "probe", return_value=permissions), patch.object(matrix, "matching_pids", return_value=set()), patch.object(matrix, "prepare", side_effect=RuntimeError("Internal task failed")), patch.object(matrix, "attack") as attack, contextlib.redirect_stdout(io.StringIO()):
                report = matrix.run(root / "output", root / "controller.json", ["textarea"], ["hid"])
            attack.assert_not_called()
            self.assertFalse(report["surfaces"][0]["baselineWorked"])
            self.assertEqual(report["surfaces"][0]["status"], "inconclusive")
