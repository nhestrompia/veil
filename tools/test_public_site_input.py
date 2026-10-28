import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_public_site_input as subject


class PublicSiteInputTests(unittest.TestCase):
    def exercise(self, bad_point=False, bad_hooks=False, input_failure=False, changed=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "browser.log"
            log.write_text("")
            session = root / "session.json"
            session.write_text(json.dumps({"target": "AgentFreeBrowserPreview", "pid": 123,
                                           "binarySHA256": "pinned", "log": str(log)}))
            binary = root / "binary"
            binary.write_bytes(b"fixed-image")
            output = root / "artifacts/attempt"
            actions = []

            def helper(arguments, **_kwargs):
                actions.append(arguments[1])
                if arguments[1] == "pause":
                    Path(arguments[2]).write_text("[]")

            def probe(arguments, *_args, **_kwargs):
                if arguments[0] == "permissions":
                    return {"postEvents": True, "desktopInputSafety": {
                        "available": True, "blockingMouseHookPIDs": [55] if bad_hooks else []}}
                if arguments[0] == "windows":
                    return {"windows": [{"kCGWindowLayer": 0, "kCGWindowBounds": {
                        "X": 100, "Y": 100, "Width": 500, "Height": 500}}]}
                if arguments[0] == "input":
                    if input_failure:
                        raise RuntimeError("posting failure")
                    log.write_text("INPUT_GATE_REFUSED type=10\n")
                    return {"status": "attempted"}
                return {"elements": []}

            import hashlib
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            data = json.loads(session.read_text())
            data["binarySHA256"] = digest
            session.write_text(json.dumps(data))
            with patch.object(subject, "ROOT", root), \
                    patch.object(subject, "pinned_image", return_value=("name", root, binary, digest)), \
                    patch.object(subject, "process_matches", return_value=not changed), \
                    patch.object(subject, "matching_pids", return_value=set()), \
                    patch.object(subject, "stop_timed_out_probe"), \
                    patch.object(subject, "probe", side_effect=probe) as calls, \
                    patch.object(subject.subprocess, "run", side_effect=helper), \
                    patch.object(subject.signal, "signal"), patch.object(subject.signal, "alarm"), \
                    patch.object(subject.time, "sleep"):
                if bad_point or bad_hooks or input_failure or changed:
                    with self.assertRaises(RuntimeError):
                        subject.run(session, output, [10, 10] if bad_point else [250, 250], True)
                else:
                    subject.run(session, output, [250, 250], True)
                result = json.loads((output / "result.json").read_text()) if output.exists() else None
                inputs = [c for c in calls.call_args_list if c.args[0][0] == "input"]
                return result, actions, len(inputs)

    def test_changed_session_sends_no_input_or_pause(self):
        result, actions, inputs = self.exercise(changed=True)
        self.assertIsNone(result)
        self.assertEqual(actions, [])
        self.assertEqual(inputs, 0)

    def test_outside_point_restores_apps_without_input(self):
        result, actions, inputs = self.exercise(bad_point=True)
        self.assertTrue(result["restored"])
        self.assertEqual(actions, ["pause", "restore"])
        self.assertEqual(inputs, 0)

    def test_remaining_mouse_hook_restores_apps_without_input(self):
        result, actions, inputs = self.exercise(bad_hooks=True)
        self.assertTrue(result["restored"])
        self.assertEqual(actions, ["pause", "restore"])
        self.assertEqual(inputs, 0)

    def test_posting_failure_still_restores_apps(self):
        result, actions, inputs = self.exercise(input_failure=True)
        self.assertTrue(result["restored"])
        self.assertEqual(actions, ["pause", "restore"])
        self.assertEqual(inputs, 1)

    def test_attempt_records_refusals_without_assigning_a_pass(self):
        result, _, inputs = self.exercise()
        self.assertEqual(inputs, 1)
        self.assertEqual(result["acceptedEvents"], 0)
        self.assertEqual(result["refusedEvents"], 1)
        self.assertEqual(result["websiteTaskOutcome"], "requires-physical-review-or-readable-page-evidence")

    def test_missing_pause_approval_does_not_read_or_launch(self):
        with self.assertRaises(ValueError):
            subject.run(Path("unused"), Path("unused"), [200, 200], False)


if __name__ == "__main__":
    unittest.main()
