import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_device_session as device


class DeviceSessionTests(unittest.TestCase):
    def test_unsupported_session_target_is_refused_before_process_access(self):
        with patch.object(device, "process_matches") as matches:
            with self.assertRaisesRegex(RuntimeError, "Unsupported physical-session"):
                device.active({"target": "UnrelatedApp"})
            matches.assert_not_called()

    def test_preview_requires_pinned_hash_and_returns_exact_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "dist/AgentFreeBrowserPreview.app/Contents/MacOS/AgentFreeBrowserPreview"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"pinned preview")
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            manifest = root / "docs/evidence/integrated-browser-permission-manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"executableSHA256": digest}))
            session = {"target": "AgentFreeBrowserPreview", "pid": 12345, "binarySHA256": digest}
            with patch.object(device, "ROOT", root), patch.object(device, "process_matches", return_value=True) as matches:
                self.assertEqual(device.active(session), binary)
                matches.assert_called_once_with(12345, binary)
                matches.reset_mock()
                with self.assertRaisesRegex(RuntimeError, "pinned consent image"):
                    device.active({**session, "binarySHA256": "0" * 64})
                matches.assert_not_called()
                binary.write_bytes(b"changed preview")
                with self.assertRaisesRegex(RuntimeError, "changed after session start"):
                    device.active(session)

    def test_failed_readiness_cleans_exact_launched_app(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.json"
            launcher = Mock()
            binary = Path(directory) / "research-binary"
            with patch.object(device, "matching_pids", return_value=set()), patch.object(device, "Oracle"), patch.object(device, "launch", return_value=(launcher, binary)), patch.object(device, "ready", side_effect=RuntimeError("not ready")), patch.object(device, "stop_launched", return_value=True) as stop:
                with self.assertRaisesRegex(RuntimeError, "not ready"):
                    device.start(path)
            stop.assert_called_once_with(launcher, binary, None)
            launcher.terminate.assert_called_once()
            launcher.wait.assert_called_once_with(timeout=3)
            self.assertFalse(path.exists())

    def session_files(self, root, verdict="inconclusive", tap="hid"):
        binary = root / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"probe identity")
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        log = root / "session.log"
        log.write_text("DEVICE_KEYBOARD bound=true\n")
        path = root / "session.json"
        path.write_text(json.dumps({"pid": 12345, "trial": {"id": "local"}, "log": str(log), "binarySHA256": "candidate"}))
        controls = root / "controls.json"
        controls.write_text(json.dumps({"postTap": tap, "results": [{"target": "InspectableControl",
            "route": "pid-hid", "repetition": 0, "verdict": verdict,
            "attempt": {"probeBinarySHA256": digest}}]}))
        return path, controls

    def test_failed_control_sends_no_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, controls = self.session_files(root)
            permission = {"postEvents": True, "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            oracle = Mock()
            oracle.state.return_value = {"submissions": [{"accepted": True}]}
            with patch.object(device, "ROOT", root), patch.object(device, "active"), patch.object(device, "Oracle", return_value=oracle), patch.object(device, "probe", return_value=permission) as probe, contextlib.redirect_stdout(io.StringIO()):
                device.attack(path, controls, 1, True, ["pid-hid"])
            self.assertEqual(probe.call_count, 1)
            self.assertEqual(probe.call_args.args[0], ["permissions"])
            result = json.loads((root / "device-session-attacks/results.json").read_text())["results"][0]
            self.assertTrue(result["skipped"])
            self.assertEqual(result["verdict"], "inconclusive")

    def test_control_insertion_point_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, controls = self.session_files(root, tap="session")
            oracle = Mock()
            oracle.state.return_value = {"submissions": [{"accepted": True}]}
            permission = {"postEvents": True, "desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}}
            with patch.object(device, "active"), patch.object(device, "Oracle", return_value=oracle), patch.object(device, "probe", return_value=permission), self.assertRaisesRegex(RuntimeError, "insertion point"):
                device.attack(path, controls, 1, True, ["pid-hid"])

    def test_no_physical_declaration_stops_before_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, controls = self.session_files(root)
            oracle = Mock()
            oracle.state.return_value = {"submissions": [{"accepted": True}]}
            with patch.object(device, "active"), patch.object(device, "Oracle", return_value=oracle), patch.object(device, "probe") as probe, self.assertRaisesRegex(RuntimeError, "physical completion"):
                device.attack(path, controls, 1, False, ["pid-hid"])
            probe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
