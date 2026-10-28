import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_preview_native_comparison as comparison


class PreviewNativeComparisonTests(unittest.TestCase):
    def exercise(self, root, result=None, failure=None, remaining=None, executed=False):
        plan = root / "docs/evidence/preview-input-resume-plan.json"
        plan.parent.mkdir(parents=True)
        plan.write_text(json.dumps({"approved": True, "executed": executed}))
        session = root / "artifacts/integrated-browser-134/physical-session/session.json"
        session.parent.mkdir(parents=True)
        session.write_text("{}")
        (root / "artifacts/integrated-browser-135").mkdir()
        calls = []

        def helper(arguments, **_kwargs):
            calls.append(arguments[1])
            if arguments[1] == "pause":
                Path(arguments[2]).write_text('["com.lujjjh.LinearMouse"]')

        with patch.object(comparison, "ROOT", root), patch.object(comparison.os, "getuid", return_value=501), patch.object(comparison, "active"), patch.object(comparison.signal, "signal"), patch.object(comparison.signal, "alarm"), patch.object(comparison.subprocess, "run", side_effect=helper), patch.object(comparison, "probe", return_value={"desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}), patch.object(comparison, "matching_pids", return_value=set(remaining or [])), patch.object(comparison, "run", return_value=result, side_effect=failure) as run:
            if executed or failure or remaining:
                with self.assertRaises(RuntimeError):
                    comparison.main()
            else:
                comparison.main()
        return calls, run.call_count

    def test_attack_failure_restores_original_apps(self):
        with tempfile.TemporaryDirectory() as directory:
            calls, count = self.exercise(Path(directory), failure=RuntimeError("reference failed"))
            self.assertEqual(calls, ["pause", "restore"])
            self.assertEqual(count, 1)

    def test_inconclusive_route_stops_next_route(self):
        with tempfile.TemporaryDirectory() as directory:
            calls, count = self.exercise(Path(directory), result={"controls": [], "results": [{"verdict": "inconclusive"}]})
            self.assertEqual(calls, ["pause", "restore"])
            self.assertEqual(count, 1)

    def test_live_probe_prevents_modifier_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            calls, _ = self.exercise(Path(directory), result={"controls": [], "results": []}, remaining=[12])
            self.assertEqual(calls, ["pause"])

    def test_completed_approval_cannot_run_again(self):
        with tempfile.TemporaryDirectory() as directory:
            calls, count = self.exercise(Path(directory), executed=True)
            self.assertEqual(calls, [])
            self.assertEqual(count, 0)
