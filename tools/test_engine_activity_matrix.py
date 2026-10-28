import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_engine_activity_matrix as matrix


def trial(status, resume=True):
    return {"runs": [{"status": status, "candidate": {"acceptedInputEvents": 0},
                      "privateResumeCompleted": resume, "privateResumeNewActions": int(resume),
                      "candidateCleanupVerified": True, "sinkCleanupVerified": True,
                      "secureInputAfterCleanup": False}]}


class EngineActivityMatrixTests(unittest.TestCase):
    def compare(self, directory, results):
        with patch.object(matrix, 'engine_environment'), patch.object(matrix, 'build_diagnostic'), \
             patch.object(matrix, 'run_focus', side_effect=results) as run_focus:
            report = matrix.run(Path(directory) / 'matrix', Path('controller'), Path('engine'), ['password-focus'])
            persisted = json.loads((Path(directory) / 'matrix/results.json').read_text())
            self.assertEqual(report, persisted)
            return report, run_focus.call_count

    def test_missing_native_action_skips_the_stable_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            report, calls = self.compare(directory, [trial('inconclusive')])
            self.assertEqual(calls, 1)
            self.assertTrue(report['cases'][1]['skipped'])
            self.assertEqual(report['cases'][1]['status'], 'inconclusive')

    def test_a_failed_resume_cannot_hide_an_observed_stable_action(self):
        with tempfile.TemporaryDirectory() as directory:
            report, calls = self.compare(directory, [trial('autonomous-website-action'), trial('autonomous-website-action', False)])
            self.assertEqual(calls, 2)
            self.assertEqual(report['cases'][1]['status'], 'autonomous-website-action')
            self.assertIn('stopReason', report)

    def test_no_action_with_a_failed_resume_remains_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            report, _ = self.compare(directory, [trial('autonomous-website-action'), trial('no-action-observed', False)])
            self.assertEqual(report['cases'][1]['status'], 'inconclusive')
