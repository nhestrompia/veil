import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_native


class NativeControlGateTests(unittest.TestCase):
    def test_failed_reference_never_launches_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["InspectableControl", "DeviceKeyboardExperiment"]:
                binary = root / f"dist/{name}.app/Contents/MacOS/{name}"
                binary.parent.mkdir(parents=True)
                binary.write_bytes(b"test executable identity")
            oracle = Mock()
            oracle.create.return_value = {"id": "disposable", "url": "http://127.0.0.1/test"}
            oracle.state.return_value = {"secret": "test-marker", "submissions": [], "events": []}
            permission = {"accessibility": True, "postEvents": True, "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            field = {"AXRole": "AXTextField", "AXDescription": "Enter native-input", "position": [100, 100], "size": [100, 30]}
            def response(arguments, _):
                if arguments[0] == "permissions": return permission
                if arguments[0] == "ax": return {"elements": [field]}
                return {"status": "attempted"}
            child = Mock(pid=12345)
            with patch.object(run_native, "ROOT", root), patch.object(run_native, "Oracle", return_value=oracle), patch.object(run_native, "probe", side_effect=response), patch.object(run_native, "observe_console", return_value={}), patch.object(run_native.time, "sleep"), patch.object(run_native.subprocess, "Popen", return_value=child) as launch, patch.object(run_native.subprocess, "check_output", return_value="test system"), contextlib.redirect_stdout(io.StringIO()):
                rows = run_native.run(["DeviceKeyboardExperiment"], ["hid"], 1, root / "results")
            self.assertEqual(launch.call_count, 1)
            self.assertIn("InspectableControl", launch.call_args.args[0][0])
            self.assertEqual(oracle.create.call_count, 1)
            self.assertTrue(rows[-1]["skipped"])
            self.assertEqual(rows[-1]["verdict"], "inconclusive")
            saved = json.loads((root / "results/results.json").read_text())
            self.assertEqual(saved["positiveControlTarget"], "InspectableControl")


if __name__ == "__main__":
    unittest.main()
