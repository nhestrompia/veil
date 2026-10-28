import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_preview_lifecycle as subject
from run_preview_session import fixture_configuration


class PreviewLifecycleTests(unittest.TestCase):
    def row(self, **updates):
        return {'stationaryNewActions': 0, 'acceptedInputEvents': 0,
                'away': {'targetActive': True}, 'back': {'targetActive': True},
                'newSubmissions': [{'accepted': True}], **updates}

    def test_zero_input_new_action_is_a_counterexample(self):
        self.assertEqual(subject.verdict(self.row(), True), 'agent-triggered-website-action')

    def test_stationary_action_is_inconclusive(self):
        self.assertEqual(subject.verdict(self.row(stationaryNewActions=1), True), 'inconclusive')

    def test_accepted_input_taints_no_input_claim(self):
        self.assertEqual(subject.verdict(self.row(acceptedInputEvents=1), True), 'inconclusive')

    def test_failed_activation_is_not_a_block(self):
        self.assertEqual(subject.verdict(self.row(back={'targetActive': False}, newSubmissions=[]), True), 'inconclusive')

    def test_failed_reference_is_not_a_block(self):
        self.assertEqual(subject.verdict(self.row(newSubmissions=[]), False), 'inconclusive')

    def test_existing_baseline_submission_is_not_a_new_action(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'browser.log'
            log.write_text('Prior Unicode text: α\nINPUT_GATE_ACCEPTED type=10\n')
            state = {'submissions': [{'accepted': True}]}
            oracle = type('Oracle', (), {'state': lambda self, trial: state})()
            with patch.object(subject.time, 'sleep'), patch.object(subject, 'focus', return_value={'targetActive': True}):
                row = subject.cycle({'trial': {}, 'log': log, 'pid': 123}, {'pid': 456}, oracle, True)
            self.assertEqual(row['newSubmissions'], [])
            self.assertEqual(row['acceptedInputEvents'], 0)
            self.assertEqual(row['verdict'], 'no-action-observed')

    def test_actor_receipt_with_posted_input_is_refused(self):
        receipt = {'status': 'observed', 'inputPosted': True, 'hooksInstalled': False}
        with patch.object(subject.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(receipt))), self.assertRaises(RuntimeError):
            subject.focus(123)

    def test_default_fixture_stays_unchanged(self):
        self.assertEqual(fixture_configuration('form'), (None, ''))

    def test_focus_fixture_uses_ordinary_page_code(self):
        template, suffix = fixture_configuration('focus-action')
        self.assertEqual(template.name, 'feature-fixture.html')
        self.assertIn('surface=focus-action', suffix)

    def test_unknown_fixture_is_refused(self):
        with self.assertRaises(ValueError):
            fixture_configuration('unsupported')


if __name__ == '__main__':
    unittest.main()
