"""Keep public-app consent attribution separate from diagnostic execution."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import launch_focus_browser as subject


class FocusBrowserLaunchTests(unittest.TestCase):
    def test_public_app_uses_launch_services_without_loader_overrides(self):
        binary = Path('/workspace/dist/AgentFreeBrowserEngine.app/Contents/MacOS/AgentFreeBrowserEngine')
        environment = {'PATH': '/usr/bin:/bin', 'DYLD_FRAMEWORK_PATH': '/workspace/engine',
                       '__XPC_DYLD_LIBRARY_PATH': '/workspace/engine',
                       'AFB_RESEARCH_FRAMEWORK_ROOT': '/workspace/engine'}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(subject, 'verified_target', return_value=(binary, environment)), \
                patch.object(subject, 'matching_pids', return_value=set()), \
                patch.object(subject.subprocess, 'Popen', return_value=Mock()) as popen:
            log = Path(directory) / 'permission.log'
            process, actual = subject.launch(log, ['--permissions'])
            command = popen.call_args.args[0]
            self.assertEqual(command[:4], ['open', '-n', '-W', str(binary.parents[2])])
            self.assertEqual(command[-2:], ['--args', '--permissions'])
            self.assertEqual(popen.call_args.kwargs['env'], {'PATH': '/usr/bin:/bin'})
            self.assertEqual(process.research_existing_pids, set())
            self.assertEqual(actual, binary)
            self.assertTrue(log.exists())

    def test_running_browser_refuses_before_another_launch(self):
        with patch.object(subject, 'verified_target', return_value=(Path('/app'), {})), \
                patch.object(subject, 'matching_pids', return_value={42}), \
                patch.object(subject.subprocess, 'Popen') as popen, \
                self.assertRaisesRegex(RuntimeError, 'already runs'):
            subject.launch(Path('/unused'), ['--permissions'])
        popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
