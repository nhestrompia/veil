"""Check fixed progress staging and readiness before any privileged run."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import unittest

from observe_renderer_signals import read_native
from prepare_renderer_identity_run import stage_script
from run_renderer_progress_comparison import REVIEWED_COMMAND_SHA256, verify_inputs


class ProgressStageTests(unittest.TestCase):
    def setUp(self):
        self.stage = Path(subprocess.run(['/usr/bin/mktemp', '-d', '/private/tmp/agentfreebrowser-renderer.XXXXXX'],
            capture_output=True, text=True, check=True).stdout.strip())
        self.stage.chmod(0o711)
        self.addCleanup(self.cleanup)
        self.native = {'host': {'path': str(self.stage / 'RendererProgressProbe.app/Contents/MacOS/RendererProgressProbe')},
            'progressControl': True, 'identityControl': True, 'javascriptPassed': True, 'snapshotPassed': True,
            'baselineSnapshotPassed': True, 'serviceIdentityStable': True}
        self.log = self.stage / 'observation.log'
        self.write_log(b'RENDERER_PROGRESS_READY ')

    def cleanup(self):
        self.stage.chmod(0o700)
        shutil.rmtree(self.stage)

    def write_log(self, prefix):
        self.log.chmod(0o600) if self.log.exists() else None
        self.log.write_bytes(prefix + json.dumps(self.native).encode() + b'\n')
        self.log.chmod(0o444)

    def test_ready_before_final_report_is_accepted(self):
        self.assertEqual(read_native(self.stage, {'manifest': []}, owner=os.getuid(), progress_ready=True), self.native)

    def test_final_report_cannot_replace_readiness(self):
        self.write_log(b'HEADLESS_RENDERER_RESULT ')
        self.assertIsNone(read_native(self.stage, {'manifest': []}, owner=os.getuid(), progress_ready=True))

    def test_failed_progress_baseline_refuses(self):
        self.native['baselineSnapshotPassed'] = False
        self.write_log(b'RENDERER_PROGRESS_READY ')
        with self.assertRaises(ValueError):
            read_native(self.stage, {'manifest': []}, owner=os.getuid(), progress_ready=True)

    def test_identity_host_is_not_progress_host(self):
        self.native['host']['path'] = str(self.stage / 'RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe')
        self.write_log(b'RENDERER_PROGRESS_READY ')
        with self.assertRaises(ValueError):
            read_native(self.stage, {'manifest': []}, owner=os.getuid(), progress_ready=True)

    def test_non_boolean_profile_refuses(self):
        with self.assertRaises(ValueError):
            stage_script([], os.getuid(), {}, progress='unrelated')

    def test_original_observation_command_is_byte_identical(self):
        path = Path(__file__).resolve().parents[1] / 'docs/evidence/renderer-metadata-reviewed-run-plan.json'
        plan = json.loads(path.read_text())
        script = stage_script(plan['manifest'], plan['preflight']['compiledUID'], plan['libraries'], observe_signals=True)
        command = '/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C /bin/sh -c ' + shlex.quote(script)
        self.assertEqual(hashlib.sha256(command.encode()).hexdigest(), plan['administratorCommandSHA256'])

    def test_self_declared_command_replacement_refuses(self):
        command = 'unrelated command'
        plan = {'maximumRuns': 1, 'repeatOnFailure': False, 'administratorCommand': command,
                'administratorCommandSHA256': hashlib.sha256(command.encode()).hexdigest()}
        self.assertNotEqual(plan['administratorCommandSHA256'], REVIEWED_COMMAND_SHA256)
        with self.assertRaises(ValueError): verify_inputs(plan)


if __name__ == '__main__':
    unittest.main()
