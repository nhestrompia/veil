import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import agent_browser as subject


class AgentBrowserTests(unittest.TestCase):
    def test_start_spawns_real_runner_in_agent_only_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'artifacts/run'
            worker = Mock()
            worker.pid = 42

            def spawn(command, **kwargs):
                output.mkdir()
                for name in ['session.json', 'AGENT-TASK.md', 'attempt-template.json']:
                    (output / name).write_text('{}')
                self.assertEqual(command[1], str(root / 'tools/website_challenge.py'))
                self.assertEqual(command[command.index('--mode') + 1], 'agent-only')
                self.assertTrue(kwargs['start_new_session'])
                self.assertNotIn('--request-permissions', command)
                return worker

            with patch.object(subject, 'ROOT', root), patch.object(subject, 'pinned_image'), \
                    patch.object(subject.subprocess, 'Popen', side_effect=spawn), \
                    patch.object(subject, 'status', return_value={'running': True, 'pid': 123}):
                result = subject.start('engine', output, 60, 'model',
                                       'https://example.org/', 'Read the heading')
            self.assertEqual(result['pid'], 123)
            worker.terminate.assert_not_called()

    def test_invalid_task_never_starts_worker(self):
        with patch.object(subject.subprocess, 'Popen') as spawn, self.assertRaises(ValueError):
            subject.start('engine', Path('/unused'), 60, '', 'file:///tmp/page', 'Read it')
        spawn.assert_not_called()

    def test_start_failure_requests_only_its_session_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'artifacts/run'
            worker = Mock()
            worker.poll.return_value = 1

            def spawn(*args, **kwargs):
                output.mkdir()
                (output / 'session.json').write_text('{"error":"startup refused"}')
                return worker

            with patch.object(subject, 'ROOT', root), patch.object(subject, 'pinned_image'), \
                    patch.object(subject.subprocess, 'Popen', side_effect=spawn), \
                    self.assertRaisesRegex(RuntimeError, 'startup refused'):
                subject.start('engine', output, 60, '', 'https://example.org/', 'Read it')
            self.assertTrue((output / 'stop').exists())
            worker.terminate.assert_not_called()

    def test_status_reports_startup_gate_without_claiming_page_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'artifacts/run'
            output.mkdir(parents=True)
            binary = root / 'browser'
            session = {'target': 'AgentFreeBrowserEngine', 'binaryPath': str(binary),
                       'appPath': str(root / 'app'), 'binarySHA256': 'pinned', 'pid': 123,
                       'status': 'running', 'humanAssistanceRequestedByRunner': False}
            (output / 'session.json').write_text(json.dumps(session))
            (output / 'browser.log').write_text('STARTUP_ADDRESS pendingPhysicalSubmit=true\n')
            with patch.object(subject, 'ROOT', root), \
                    patch.object(subject, 'pinned_image', return_value=('name', root / 'app', binary, 'pinned')), \
                    patch.object(subject, 'process_matches', return_value=True):
                result = subject.status(output / 'session.json')
            self.assertTrue(result['running'])
            self.assertTrue(result['startupAddressGateLogged'])
            self.assertFalse(result['contentProcessReported'])
            self.assertFalse(result['humanAssistanceRequestedByRunner'])
            self.assertEqual(result['websiteOutcome'], 'not-independently-scored')

    def test_stop_ignores_an_untrusted_stop_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'artifacts/run/session.json'
            path.parent.mkdir(parents=True)
            untrusted = root / 'unrelated-file'
            with patch.object(subject, 'ROOT', root), \
                    patch.object(subject, 'status', return_value={'ownedHostStopped': True, 'stopFile': str(untrusted)}):
                subject.stop(path)
            self.assertTrue((path.parent / 'stop').exists())
            self.assertFalse(untrusted.exists())


if __name__ == '__main__':
    unittest.main()
