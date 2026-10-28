import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_veil_native_input as subject


class VeilNativeApprovalTests(unittest.TestCase):
    def test_no_probe_or_pause_without_fresh_approval(self):
        for approved, executed in [(False, False), (True, True)]:
            with self.subTest(approved=approved, executed=executed), tempfile.TemporaryDirectory() as directory:
                plan = Path(directory) / 'plan.json'
                plan.write_text(json.dumps({'approved': approved, 'executed': executed}))
                with patch.object(subject.os, 'getuid', return_value=501), \
                        patch.object(subject, 'probe') as probe, \
                        patch.object(subject.subprocess, 'run') as run:
                    with self.assertRaisesRegex(RuntimeError, 'fresh ordinary-user approval'):
                        subject.run(plan)
                    probe.assert_not_called()
                    run.assert_not_called()

    def test_changed_runner_stops_before_session_or_input(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / 'plan.json'
            plan.write_text(json.dumps({'approved': True, 'executed': False, 'runnerSHA256': 'wrong'}))
            with patch.object(subject.os, 'getuid', return_value=501), \
                    patch.object(subject, 'probe') as probe, \
                    patch.object(subject.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'Reviewed runner changed'):
                    subject.run(plan)
                probe.assert_not_called()
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
