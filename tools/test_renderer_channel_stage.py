import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from observe_renderer_channel import read_channel_stage
from observe_renderer_signals import private_stages
from prepare_renderer_channel_run import prepare, stage_script, validate_url, HELPER, APP_NAMES
from prepare_renderer_identity_run import bounded_tool
import run_renderer_channel_comparison as comparison


class ChannelStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = Path(tempfile.mkdtemp(prefix='afb-channel-tests-', dir='/private/tmp'))
        cls.plan = prepare(cls.directory / 'plan.json')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.directory)

    def test_exact_staging_rehearsal_has_only_expected_root_refusal(self):
        before = private_stages()
        script = stage_script(self.plan['manifest'], os.getuid(), self.plan['libraries'], self.plan['fixtureURL'], stage_uid=os.getuid())
        result = subprocess.run(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL=C',
                                 '/bin/sh', '-c', script], capture_output=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = [json.loads(line.removeprefix('STAGING_RESULT ')) for line in result.stdout.decode().splitlines()
                  if line.startswith('STAGING_RESULT ')]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['helperExitCode'], 64)
        self.assertTrue(values[0]['stagingRemoved'])
        self.assertFalse(Path(values[0]['temporaryDirectory']).exists())
        self.assertNotIn(b'CHANNEL_LAUNCHER_READY', result.stdout)
        self.assertEqual(private_stages(), before)

    def test_failed_dependency_tool_cannot_reach_helper(self):
        def failing_tool(command, arguments):
            if command == '/usr/bin/otool' and arguments[0] == '-L':
                return "/usr/bin/printf 'image:\\n/usr/lib/libSystem.B.dylib\\n'; exit 73"
            return bounded_tool(command, arguments)
        before = private_stages()
        with patch('prepare_renderer_channel_run.bounded_tool', side_effect=failing_tool):
            script = stage_script(self.plan['manifest'], os.getuid(), self.plan['libraries'], self.plan['fixtureURL'], stage_uid=os.getuid())
        result = subprocess.run(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL=C',
                                 '/bin/sh', '-c', script], capture_output=True, timeout=40)
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertNotIn(b'CHANNEL_LAUNCHER_READY', result.stdout)
        self.assertEqual(private_stages(), before)

    def test_missing_manifest_item_refuses(self):
        with self.assertRaises(ValueError):
            stage_script(self.plan['manifest'][:-1], os.getuid(), self.plan['libraries'], self.plan['fixtureURL'])

    def test_extra_manifest_item_refuses(self):
        with self.assertRaises(ValueError):
            stage_script([*self.plan['manifest'], self.plan['manifest'][0]], os.getuid(), self.plan['libraries'], self.plan['fixtureURL'])

    def test_extra_dependency_profile_refuses(self):
        with self.assertRaises(ValueError):
            stage_script(self.plan['manifest'], os.getuid(), {**self.plan['libraries'], 'other': []}, self.plan['fixtureURL'])

    def test_noncanonical_or_external_addresses_refuse(self):
        for url in ('https://127.0.0.1:8767/channel/0123456789abcdef', 'http://localhost:8767/channel/0123456789abcdef',
                    'http://127.0.0.1:80/channel/0123456789abcdef', 'http://127.0.0.1:08767/channel/0123456789abcdef',
                    'http://127.0.0.1:8767/channel/0123456789abcdef?extra=1',
                    'http://127.0.0.1:8767/channel/0123456789abcdef#fragment',
                    'http://user@127.0.0.1:8767/channel/0123456789abcdef',
                    'http://127.0.0.1:8767/channel/0123456789abcdeg'):
            with self.subTest(url=url), self.assertRaises(ValueError): validate_url(url)

    def test_command_checks_before_sealing_or_execution(self):
        script = stage_script(self.plan['manifest'], os.getuid(), self.plan['libraries'], self.plan['fixtureURL'])
        self.assertLess(script.index('shasum'), script.index('/bin/chmod 0711'))
        self.assertLess(script.index('--verify'), script.index('--root-channel'))
        self.assertNotIn('rm -rf', script)
        self.assertNotIn('launchctl', script)

    def test_reviewed_plan_pin_rejects_a_changed_allowance(self):
        digest = hashlib.sha256((json.dumps(self.plan, indent=2) + '\n').encode()).hexdigest()
        with patch.object(comparison, 'REVIEWED_PLAN_SHA256', digest), patch.object(
                comparison, 'REVIEWED_COMMAND_SHA256', self.plan['administratorCommandSHA256']):
            comparison.verify_inputs(self.plan)
            changed = dict(self.plan, maximumRuns=2)
            with self.assertRaises(ValueError): comparison.verify_inputs(changed)

    def test_consumed_allowance_refuses_before_any_launch(self):
        digest = hashlib.sha256((json.dumps(self.plan, indent=2) + '\n').encode()).hexdigest()
        marker = self.directory / 'consumed.json'
        marker.write_text('{}\n')
        with patch.object(comparison, 'PLAN', self.directory / 'plan.json'), patch.object(
                comparison, 'CONSUMED', marker), patch.object(comparison, 'REVIEWED_PLAN_SHA256', digest), patch.object(
                comparison, 'REVIEWED_COMMAND_SHA256', self.plan['administratorCommandSHA256']), patch.object(
                comparison.subprocess, 'Popen') as launch:
            with self.assertRaises(ValueError):
                comparison.run(Path(__file__).resolve().parents[1] / 'artifacts/not-created-consumed-test')
            launch.assert_not_called()


class ChannelObserverTests(unittest.TestCase):
    def setUp(self):
        self.stage = Path(subprocess.run(['/usr/bin/mktemp', '-d', '/private/tmp/agentfreebrowser-renderer.XXXXXX'],
            check=True, capture_output=True, text=True).stdout.strip())
        self.stage.chmod(0o711)
        self.addCleanup(shutil.rmtree, self.stage)
        self.log = self.stage / 'observation.log'
        self.helper = self.stage / HELPER
        self.helper.write_bytes(b'fake-fixed-supervisor')
        self.helper.chmod(0o700)
        self.plan = {'fixtureURL': 'http://127.0.0.1:8767/channel/0123456789abcdef', 'ordinaryUID': os.getuid(),
            'ordinaryGID': os.getgid(), 'isolatedUID': 4294967294, 'isolatedGID': 4294967294,
            'manifest': [{'staged': HELPER, 'size': self.helper.stat().st_size, 'sha256': hashlib.sha256(self.helper.read_bytes()).hexdigest()}]}
        def identity(pid, index, isolated):
            uid = gid = 4294967294
            if not isolated: uid, gid = os.getuid(), os.getgid()
            return {'pid': pid, 'startedSeconds': 100, 'startedMicroseconds': 200,
                'path': str(self.stage / (APP_NAMES[index] + '.app/Contents/MacOS/' + APP_NAMES[index])),
                'realUID': uid, 'effectiveUID': uid, 'savedUID': uid,
                'realGID': gid, 'effectiveGID': gid, 'savedGID': gid}
        self.launch = {'rendererPID': 101, 'displayPID': 102, 'watchdogPID': 103, 'ordinaryUID': os.getuid(),
            'rendererUID': 4294967294, 'displayUID': os.getuid(), 'rootRun': True, 'permanentDropChecked': True}
        self.native = {'host': identity(101, 0, True), 'services': {role: identity(104 + i, 0, True)
            for i, role in enumerate(('content', 'gpu', 'network'))}, 'sample': {'nonce': '0123456789abcdef'}}
        self.display = {'host': identity(102, 1, False)}
        self.write()

    def bytes(self):
        return b''.join(prefix.encode() + b' ' + json.dumps(value).encode() + b'\n' for prefix, value in (
            ('CHANNEL_LAUNCHER_READY', self.launch), ('CHANNEL_ATTACK_READY', self.native),
            ('CHANNEL_DISPLAY_READY', self.display), ('CHANNEL_FRAME_PRESENTED', {'count': 1})))

    def write(self, raw=None):
        if self.log.exists(): self.log.chmod(0o600)
        self.log.write_bytes(self.bytes() if raw is None else raw)
        self.log.chmod(0o444)

    def read(self):
        return read_channel_stage(self.stage, self.plan, owner=os.getuid())

    def test_bound_readiness(self):
        self.assertEqual(self.read()['native'], self.native)

    def test_no_newline_waits_without_json_parse(self):
        self.write(b'CHANNEL_LAUNCHER_READY {"rendererPID":')
        self.assertIsNone(self.read())

    def test_partial_last_record_waits(self):
        self.write(self.bytes().rsplit(b'\n', 2)[0] + b'\nCHANNEL_FRAME_PRESENTED {"count":')
        self.assertIsNone(self.read())

    def test_duplicate_readiness_refuses(self):
        self.write(self.bytes() + b'CHANNEL_ATTACK_READY ' + json.dumps(self.native).encode() + b'\n')
        with self.assertRaises(ValueError): self.read()

    def test_wrong_fixture_refuses(self):
        self.native['sample']['nonce'] = 'fedcba9876543210'
        self.write()
        with self.assertRaises(ValueError): self.read()

    def test_other_app_refuses(self):
        self.display['host']['path'] = '/unrelated/application'
        self.write()
        with self.assertRaises(ValueError): self.read()

    def test_wrong_credentials_refuse(self):
        self.native['services']['content']['savedUID'] = os.getuid()
        self.write()
        with self.assertRaises(ValueError): self.read()

    def test_wrong_host_pid_refuses(self):
        self.launch['rendererPID'] = 999
        self.write()
        with self.assertRaises(ValueError): self.read()

    def test_boolean_identity_refuses(self):
        self.native['host']['startedMicroseconds'] = False
        self.write()
        with self.assertRaises(ValueError): self.read()

    def test_writable_log_refuses(self):
        self.log.chmod(0o644)
        with self.assertRaises(ValueError): self.read()

    def test_private_stage_waits(self):
        self.stage.chmod(0o700)
        self.assertIsNone(self.read())

    def test_root_only_helper_metadata_change_refuses(self):
        self.helper.chmod(0o755)
        with self.assertRaises(ValueError): self.read()

    def test_changed_readable_image_refuses(self):
        image = self.stage / 'fake-image'
        image.write_bytes(b'fixed-image')
        image.chmod(0o444)
        self.plan['manifest'].append({'staged': image.name, 'size': image.stat().st_size,
            'sha256': hashlib.sha256(image.read_bytes()).hexdigest()})
        self.assertIsNotNone(self.read())
        image.chmod(0o600)
        image.write_bytes(b'wrong-image')
        image.chmod(0o444)
        with self.assertRaises(ValueError): self.read()

    def test_image_symlink_refuses(self):
        target = self.stage / 'target'
        target.write_bytes(b'fixed-image')
        image = self.stage / 'fake-image'
        image.symlink_to(target)
        self.plan['manifest'].append({'staged': image.name, 'size': target.stat().st_size,
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        with self.assertRaises(OSError): self.read()


if __name__ == '__main__':
    unittest.main()
