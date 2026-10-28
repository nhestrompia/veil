import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_inspector_discovery_control as runner


class DiscoveryResultTests(unittest.TestCase):
    def check_result(self, submissions, cleanup_error=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / ".build/inspector-discovery-control"
            binary.parent.mkdir()
            binary.write_bytes(b"test helper")
            output = root / "artifacts/control"
            server = Mock(server_port=12345, controller_key="test-only")
            worker = Mock(ident=1)
            worker.is_alive.side_effect = [True, False]
            oracle = Mock()
            oracle.state.return_value = {"submissions": submissions}
            reference = {"pid": 123, "trial": {"url": "http://127.0.0.1:12345/trial/0123456789abcdef"}}
            completed = subprocess.CompletedProcess([], 0, json.dumps({"status": "reference-discovered"}), "")
            with patch.object(runner, "ROOT", root), patch.object(runner, "matching_pids", return_value=set()), patch.object(runner, "FixtureServer", return_value=server), patch.object(runner.threading, "Thread", return_value=worker), patch.object(runner, "Oracle", return_value=oracle), patch.object(runner, "prepare", return_value=reference), patch.object(runner.subprocess, "run", return_value=completed), patch.object(runner, "close", side_effect=cleanup_error) as close:
                if cleanup_error:
                    with self.assertRaises(RuntimeError):
                        runner.run(output)
                else:
                    runner.run(output)
            close.assert_called_once_with(reference)
            server.shutdown.assert_called_once()
            server.server_close.assert_called_once()
            return json.loads((output / "results.json").read_text())

    def test_unexpected_task_action_invalidates_discovery(self):
        result = self.check_result([{"accepted": True}])
        self.assertEqual(result["status"], "inconclusive")
        self.assertIn("unexpectedly submitted", result["error"])

    def test_failed_reference_cleanup_invalidates_saved_discovery(self):
        result = self.check_result([], RuntimeError("test cleanup failed"))
        self.assertEqual(result["status"], "inconclusive")
        self.assertTrue(result["fixtureStopped"])

    def test_clean_discovery_retains_its_distinct_success_status(self):
        result = self.check_result([])
        self.assertEqual(result["status"], "reference-discovered")
        self.assertTrue(result["referenceCleanupVerified"])


if __name__ == "__main__":
    unittest.main()
