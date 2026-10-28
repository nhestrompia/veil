import json
import hashlib
from pathlib import Path
import subprocess
import plistlib
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_inspector_discovery_control as runner


class DiscoveryResultTests(unittest.TestCase):
    def test_bundle_timeout_stops_only_its_verified_helper_and_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            binary = output / "InspectorDiscoveryControl.app/Contents/MacOS/InspectorDiscoveryControl"
            launcher = Mock()
            launcher.wait.side_effect = [subprocess.TimeoutExpired("test launcher", 18), 0]
            launcher.poll.return_value = None
            with patch.object(runner.subprocess, "Popen", return_value=launcher), patch.object(runner, "stop_launched", return_value=True) as stop:
                with self.assertRaises(subprocess.TimeoutExpired):
                    runner.invoke_bundle(["123", "test-fixture"], output, binary)
            stop.assert_called_once_with(launcher, binary)
            launcher.terminate.assert_called_once()

    def test_changed_bundle_identity_or_image_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            app = root / "dist/InspectorDiscoveryControl.app"
            binary = app / "Contents/MacOS/InspectorDiscoveryControl"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"test comparison image")
            info = app / "Contents/Info.plist"
            identity = {"CFBundleIdentifier": "research.agentfreebrowser.inspectordiscovery"}
            info.write_bytes(plistlib.dumps(identity))
            manifest = {"path": str(app), "executableSHA256": hashlib.sha256(binary.read_bytes()).hexdigest(), "sourceHashes": {}}
            evidence = root / "docs/evidence"
            evidence.mkdir(parents=True)
            (evidence / "inspector-discovery-app-manifest.json").write_text(json.dumps(manifest))
            with patch.object(runner, "ROOT", root), patch.object(runner.subprocess, "run"):
                runner.verified_bundle(binary)
                info.write_bytes(plistlib.dumps({"CFBundleIdentifier": "unrelated"}))
                with self.assertRaises(RuntimeError):
                    runner.verified_bundle(binary)
                info.write_bytes(plistlib.dumps(identity))
                binary.write_bytes(b"changed")
                with self.assertRaises(RuntimeError):
                    runner.verified_bundle(binary)

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
