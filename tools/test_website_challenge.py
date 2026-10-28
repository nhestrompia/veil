import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import website_challenge as subject


class WebsiteChallengeTests(unittest.TestCase):
    def scaffold(self, root):
        evidence = root / "docs/evidence"
        evidence.mkdir(parents=True)
        policies = []
        for name in subject.TARGETS.values():
            binary = root / "dist" / (name + ".app") / "Contents/MacOS" / name
            binary.parent.mkdir(parents=True)
            binary.write_bytes(name.encode())
            policies.append({"name": name, "sha256": hashlib.sha256(binary.read_bytes()).hexdigest()})
        (evidence / "preview-renderer-read-permission-manifest.json").write_text(json.dumps({"targetPolicies": policies}))

    def exercise(self, target="control", grant=True, launch_failure=False, preflight_timeout=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.scaffold(root)
            output = root / "artifacts/run"
            launches = []

            def launch(name, log, arguments):
                launches.append(arguments)
                process = Mock()
                process.pid = 789
                if arguments == ["--permissions"]:
                    log.write_text(f"DEVICE_KEYBOARD permission={str(grant).lower()}\n")
                    if preflight_timeout:
                        process.wait.side_effect = [subprocess.TimeoutExpired("open", 15), None]
                else:
                    log.write_text("Browser ready: pid=123\nDEVICE_KEYBOARD permission=true openStatus=0\n")
                return process, root / "dist" / (name + ".app") / "Contents/MacOS" / name

            with patch.object(subject, "ROOT", root), patch.object(subject, "matching_pids", return_value=set()), \
                    patch.object(subject.subprocess, "run"), patch.object(subject, "launch", side_effect=launch), \
                    patch.object(subject, "ready", return_value=123, side_effect=RuntimeError("not ready") if launch_failure else None), \
                    patch.object(subject, "process_matches", side_effect=[True, False]), \
                    patch.object(subject, "stop_launched", return_value=True) as cleanup, \
                    patch.object(subject.signal, "signal"), patch.object(subject.signal, "alarm"):
                if not grant or launch_failure:
                    with self.assertRaises(RuntimeError):
                        subject.run(target, "wikipedia", output, 15)
                elif preflight_timeout:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        subject.run(target, "wikipedia", output, 15)
                else:
                    subject.run(target, "wikipedia", output, 15)
                result = json.loads((output / "session.json").read_text())
                template = json.loads((output / "attempt-template.json").read_text()) if (output / "attempt-template.json").exists() else None
                return result, template, launches, cleanup.call_args_list

    def test_all_public_tasks_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            for site in subject.SITES:
                item = subject.challenge(site)
                path = Path(directory) / "challenge.json"
                path.write_text(json.dumps(item))
                self.assertEqual(subject.load_challenge(path), item)

    def test_changed_tasks_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            for field, value in [("startURL", "https://example.org"), ("query", "changed"),
                                 ("challengeID", "1234abcd"), ("schemaVersion", 2)]:
                item = subject.challenge("google")
                item[field] = value
                path = Path(directory) / "challenge.json"
                path.write_text(json.dumps(item))
                with self.assertRaises(ValueError):
                    subject.load_challenge(path)

    def test_changed_browser_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.scaffold(root)
            binary = root / "dist/AgentFreeBrowserPreview.app/Contents/MacOS/AgentFreeBrowserPreview"
            binary.write_bytes(b"changed")
            with patch.object(subject, "ROOT", root), self.assertRaises(RuntimeError):
                subject.pinned_image("preview")

    def test_public_task_never_assigns_an_automatic_pass(self):
        session, template, launches, _ = self.exercise()
        self.assertEqual(session["status"], "browser-exited")
        self.assertTrue(session["ownedHostStopped"])
        self.assertFalse(session["pageStateObservedByRunner"])
        self.assertFalse(session["humanSetupVerified"])
        self.assertEqual(template["assessment"], "requires-independent-review")
        self.assertEqual(launches, [["--url", "https://en.wikipedia.org/"]])

    def test_preview_only_checks_existing_grant(self):
        _, _, launches, cleanup = self.exercise(target="preview")
        self.assertEqual(launches[0], ["--permissions"])
        self.assertEqual(len(cleanup), 2)
        self.assertNotIn("--request-permissions", str(launches))

    def test_ineffective_grant_does_not_launch_a_browser(self):
        session, template, launches, _ = self.exercise(target="preview", grant=False)
        self.assertEqual(session["status"], "failed")
        self.assertIsNone(template)
        self.assertEqual(launches, [["--permissions"]])

    def test_readiness_failure_still_stops_owned_browser(self):
        session, _, _, cleanup = self.exercise(launch_failure=True)
        self.assertEqual(session["status"], "failed")
        self.assertTrue(session["ownedHostStopped"])
        self.assertEqual(len(cleanup), 1)

    def test_preflight_timeout_stops_only_its_owned_process(self):
        session, _, _, cleanup = self.exercise(target="preview", preflight_timeout=True)
        self.assertEqual(session["status"], "failed")
        self.assertEqual(len(cleanup), 2)

    def test_timeout_bounds(self):
        for seconds in [0, 14, 901]:
            with self.assertRaises(ValueError):
                subject.run("control", "google", Path("unused"), seconds)


if __name__ == "__main__":
    unittest.main()
