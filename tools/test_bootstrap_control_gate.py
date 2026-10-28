import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_bootstrap_attacks as bootstrap


class BootstrapControlGateTests(unittest.TestCase):
    def test_failed_reference_readiness_skips_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"test executable identity")
            oracle = Mock()
            oracle.create.return_value = {"id": "disposable", "url": "http://127.0.0.1/test"}
            permissions = {"postEvents": True, "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            child = Mock()
            with patch.object(bootstrap, "ROOT", root), patch.object(bootstrap, "ROUTES", ["hid"]), patch.object(bootstrap, "Oracle", return_value=oracle), patch.object(bootstrap, "probe", return_value=permissions), patch.object(bootstrap, "matching_pids", return_value=set()), patch.object(bootstrap, "stop_launched", return_value=True), patch.object(bootstrap.time, "sleep"), patch.object(bootstrap.subprocess, "Popen", return_value=child) as launch, contextlib.redirect_stdout(io.StringIO()):
                bootstrap.run(root / "results", 1)
            self.assertEqual(launch.call_count, 1)
            self.assertIn("InspectableControl.app", launch.call_args.args[0][3])
            self.assertEqual(oracle.create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
