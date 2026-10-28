import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from observe_renderer_signals import read_fixed_file, read_native
from prepare_renderer_identity_run import stage_script
from run_renderer_signal_reference import ACTOR, actor_arguments


class RendererSignalObserverTests(unittest.TestCase):
    def setUp(self):
        self.stage = Path(subprocess.run(['/usr/bin/mktemp', '-d', '/private/tmp/agentfreebrowser-renderer.XXXXXX'],
            capture_output=True, text=True, check=True).stdout.strip())
        self.stage.chmod(0o711)
        self.addCleanup(self.cleanup)
        self.native = {'host': {'path': str(self.stage / 'RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe')},
                       'completed': True, 'identityControl': True, 'javascriptPassed': True,
                       'snapshotPassed': True, 'serviceIdentityStable': True, 'snapshotPNGBase64': 'fixed-fake-image'}
        self.log = self.stage / 'observation.log'
        self.log.write_bytes(self.line())
        self.log.chmod(0o444)
        self.image = self.stage / 'image'
        self.image.write_bytes(b'fixed-fake-image')
        self.image.chmod(0o444)
        self.plan = {'manifest': [{'staged': 'image', 'size': self.image.stat().st_size,
                                  'sha256': hashlib.sha256(self.image.read_bytes()).hexdigest()}]}

    def line(self):
        return b'HEADLESS_RENDERER_RESULT ' + json.dumps(self.native).encode() + b'\n'

    def cleanup(self):
        self.stage.chmod(0o700)
        shutil.rmtree(self.stage)

    def test_complete_verified_record(self):
        result = read_native(self.stage, self.plan, owner=os.getuid())
        self.assertEqual(result['host'], self.native['host'])
        self.assertNotIn('snapshotPNGBase64', result)

    def test_partial_line_waits(self):
        self.log.chmod(0o600)
        self.log.write_bytes(self.line()[:-1])
        self.log.chmod(0o444)
        self.assertIsNone(read_native(self.stage, self.plan, owner=os.getuid()))

    def test_private_staging_waits_without_reading(self):
        self.stage.chmod(0o700)
        self.assertIsNone(read_native(self.stage, self.plan, owner=os.getuid()))

    def test_writable_log_refuses(self):
        self.log.chmod(0o644)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_log_symlink_refuses(self):
        self.log.unlink()
        self.log.symlink_to(self.image)
        with self.assertRaises(OSError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_log_fifo_refuses_without_blocking(self):
        self.log.unlink()
        os.mkfifo(self.log, 0o444)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_changed_image_refuses(self):
        self.image.chmod(0o600)
        self.image.write_bytes(b'wrong-fake-image')
        self.image.chmod(0o444)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_other_host_refuses(self):
        self.native['host']['path'] = '/unrelated/app'
        self.log.chmod(0o600)
        self.log.write_bytes(self.line())
        self.log.chmod(0o444)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_failed_rendering_refuses(self):
        self.native['javascriptPassed'] = False
        self.log.chmod(0o600)
        self.log.write_bytes(self.line())
        self.log.chmod(0o444)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_duplicate_record_refuses(self):
        self.log.chmod(0o600)
        self.log.write_bytes(self.line() * 2)
        self.log.chmod(0o444)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())

    def test_only_integer_identity_arguments(self):
        identity = {'pid': 2, 'startedSeconds': 3, 'startedMicroseconds': False}
        native = {'host': identity, 'servicesAfterSnapshot': {r: {'identity': identity} for r in ('content', 'gpu', 'network')}}
        with self.assertRaises(ValueError): actor_arguments(native)

    def test_root_only_supervisor_gets_metadata_check_without_read(self):
        helper = self.stage / 'renderer-identity-supervisor'
        helper.write_bytes(b'fixed-fake-supervisor')
        helper.chmod(0o700)
        self.plan['manifest'].append({'staged': helper.name, 'size': helper.stat().st_size,
                                      'sha256': hashlib.sha256(helper.read_bytes()).hexdigest()})

        def refuse_helper_read(path, *args):
            if path == helper:
                raise PermissionError('The root-only helper is intentionally unreadable')
            return read_fixed_file(path, *args)

        with patch('observe_renderer_signals.read_fixed_file', side_effect=refuse_helper_read):
            self.assertIsNotNone(read_native(self.stage, self.plan, owner=os.getuid()))
        helper.chmod(0o600)
        with self.assertRaises(ValueError): read_native(self.stage, self.plan, owner=os.getuid())


@unittest.skipUnless(ACTOR.exists(), 'Build the separate signal actor first')
class RendererSignalActorRefusalTests(unittest.TestCase):
    def test_missing_process_reports_metadata_operation_without_signal(self):
        run = subprocess.run([str(ACTOR), '--reference', *(['2147483647', '0', '0'] * 4)],
                             capture_output=True, timeout=2)
        self.assertEqual(run.returncode, 65)
        prefix = b'SIGNAL_SCOPE_REFUSAL '
        self.assertTrue(run.stdout.startswith(prefix))
        record = json.loads(run.stdout[len(prefix):])
        self.assertEqual(record['api'], 'sysctl-kern-proc-pid')
        self.assertEqual(record['signalCallsSent'], 0)
        self.assertEqual(record['bytes'], 0)

    def test_missing_or_unknown_mode(self):
        for arguments in ([], ['--unknown', *(['2', '1', '1'] * 4)]):
            run = subprocess.run([str(ACTOR), *arguments], capture_output=True, timeout=2)
            self.assertEqual(run.returncode, 64)
            self.assertEqual(run.stdout, b'')

    def test_unrelated_live_process_refuses_without_signal(self):
        run = subprocess.run([str(ACTOR), '--reference', str(os.getpid()), '0', '0', *(['2', '1', '1'] * 3)],
                             capture_output=True, timeout=2)
        self.assertEqual(run.returncode, 66)
        self.assertEqual(run.stdout, b'')


if __name__ == '__main__':
    unittest.main()
