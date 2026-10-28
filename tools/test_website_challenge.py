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

    def exercise(self, target="control", grant=True, launch_failure=False, preflight_timeout=False, agent_label=''):
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
                    patch.object(subject.subprocess, "run"), patch.object(subject, "launch", side_effect=launch) as legacy_launch, \
                    patch.object(subject, "launch_engine", side_effect=lambda log, arguments: launch('AgentFreeBrowserEngine', log, arguments)) as engine_launch, \
                    patch.object(subject, "verified_engine_target", return_value=(root / 'dist/AgentFreeBrowserEngine.app/Contents/MacOS/AgentFreeBrowserEngine', {})), \
                    patch.object(subject, "launch_pointer", side_effect=lambda log, arguments: launch('AgentFreeBrowserPointer', log, arguments)) as pointer_launch, \
                    patch.object(subject, "verified_pointer_target", return_value=(root / 'dist/AgentFreeBrowserPointer.app/Contents/MacOS/AgentFreeBrowserPointer', {})), \
                    patch.object(subject, "launch_veil", side_effect=lambda log, arguments: launch('Veil', log, arguments)) as veil_launch, \
                    patch.object(subject, "verified_veil_target", return_value=(root / 'dist/Veil.app/Contents/MacOS/Veil', {})), \
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
                    subject.run(target, "wikipedia", output, 15, agent_label=agent_label)
                result = json.loads((output / "session.json").read_text())
                template = json.loads((output / "attempt-template.json").read_text()) if (output / "attempt-template.json").exists() else None
                if target == 'engine':
                    legacy_launch.assert_not_called()
                    self.assertGreater(engine_launch.call_count, 0)
                if target == 'pointer':
                    legacy_launch.assert_not_called()
                    engine_launch.assert_not_called()
                    self.assertGreater(pointer_launch.call_count, 0)
                return result, template, launches, cleanup.call_args_list

    def test_pointer_candidate_uses_own_native_launcher_and_existing_grant(self):
        session, template, launches, _ = self.exercise(target='pointer')
        self.assertEqual(session['target'], 'AgentFreeBrowserPointer')
        self.assertEqual(session['bundleIdentifier'], 'research.agentfreebrowser.pointer')
        self.assertEqual(launches[0], ['--permissions'])
        self.assertEqual(template['stages']['navigation'], 'not-tested')

    def test_pointer_missing_grant_stops_before_website_launch(self):
        session, template, launches, _ = self.exercise(target='pointer', grant=False)
        self.assertEqual(launches, [['--permissions']])
        self.assertIsNone(template)
        self.assertTrue(session['ownedHostStopped'])

    def test_veil_missing_grant_is_a_setup_failure(self):
        session, template, launches, _ = self.exercise(target='veil', grant=False)
        self.assertEqual(launches, [['--permissions']])
        self.assertEqual(session['bundleIdentifier'], 'research.agentfreebrowser.veil')
        self.assertIsNone(template)
        self.assertTrue(session['ownedHostStopped'])

    def test_all_public_tasks_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            for site in subject.SITES:
                item = subject.challenge(site)
                path = Path(directory) / "challenge.json"
                path.write_text(json.dumps(item))
                self.assertEqual(subject.load_challenge(path), item)

    def test_custom_task_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            item = subject.custom_challenge('https://www.wikipedia.org/', 'Open the English page and search for WebKit.')
            path = Path(directory) / 'challenge.json'
            path.write_text(json.dumps(item))
            self.assertEqual(subject.load_challenge(path), item)

    def test_custom_task_refuses_credentials_and_nonweb_schemes(self):
        for url in ['file:///tmp/page', 'javascript:alert(1)', 'http://example.org/',
                    'https://user:secret@example.org/', 'https://example.org/ bad']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                subject.custom_challenge(url, 'Search')

    def test_default_task_never_asks_for_human_setup(self):
        item = subject.custom_challenge('https://example.org/', 'Read the heading')
        session = {'target': 'AgentFreeBrowserEngine', 'pid': 123, 'appPath': '/app',
                   'binaryPath': '/app/binary', 'bundleIdentifier': 'research.browser',
                   'binarySHA256': 'pinned', 'sessionFile': '/session.json', 'maximumSessionSeconds': 600}
        text = subject.instructions(item, session)
        self.assertIn('Do not ask the human to open a page', text)
        self.assertIn('Use your own computer-use', text)
        self.assertIn('Record page clicks even outside the task target', text)
        self.assertNotIn('The human uses the built-in keyboard', text)
        self.assertNotIn('## Two separate phases', text)

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

    def test_direct_search_tasks_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            for site in subject.SITES:
                item = subject.challenge(site, search_page=True)
                path = Path(directory) / "challenge.json"
                path.write_text(json.dumps(item))
                self.assertEqual(subject.load_challenge(path), item)
                self.assertEqual(item["startURL"], subject.SEARCH_PAGES[site])

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

    def test_current_engine_uses_native_launcher_and_existing_grant(self):
        session, _, launches, cleanup = self.exercise(target='engine')
        self.assertEqual(session['target'], 'AgentFreeBrowserEngine')
        self.assertEqual(launches[0], ['--permissions'])
        self.assertEqual(len(cleanup), 2)
        self.assertNotIn('--request-permissions', str(launches))

    def test_engine_ineffective_grant_prevents_website_launch(self):
        session, template, launches, _ = self.exercise(target='engine', grant=False)
        self.assertEqual(session['status'], 'failed')
        self.assertIsNone(template)
        self.assertEqual(launches, [['--permissions']])

    def test_model_label_is_recorded_in_session_and_attempt(self):
        session, template, _, _ = self.exercise(target='engine', agent_label='MODEL_A / CLIENT')
        self.assertEqual(session['agentLabel'], 'MODEL_A / CLIENT')
        self.assertEqual(template['agent'], 'MODEL_A / CLIENT')

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
