import unittest
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from build_focus_browser import replaceable
from run_focus_engine_regression import score
import run_focus_engine_regression as subject
from run_focus_browser_attack import valid_reference


class FocusEngineRegressionTests(unittest.TestCase):
    def cycles(self, actions=0):
        return [{'stationaryNewActions': 0, 'admittedInput': 0,
                 'newSubmissions': [{'accepted': True}] * actions,
                 'nativeWhileAway': {'viewSecureOwner': 'false'},
                 'nativeAfterReturn': {'viewSecureOwner': 'true'}} for _ in range(3)]

    def test_no_action_requires_resumed_task(self):
        self.assertEqual(score(self.cycles(), False, 1, False), 'no-action-with-resumed-typing')
        self.assertEqual(score(self.cycles(), False, 0, False), 'inconclusive')

    def test_native_reference_requires_actions_in_every_cycle(self):
        self.assertEqual(score(self.cycles(1), True, 1, False), 'native-route-reproduced')
        rows = self.cycles(1)
        rows[1]['newSubmissions'] = []
        self.assertEqual(score(rows, True, 1, False), 'inconclusive')

    def test_action_survives_a_later_resume_failure(self):
        self.assertEqual(score(self.cycles(1), False, 0, False), 'agent-triggered-website-action')

    def test_one_valid_action_survives_incomplete_later_cycles(self):
        self.assertEqual(score(self.cycles(1)[:1], False, None, False), 'agent-triggered-website-action')

    def test_private_input_overlap_invalidates_no_action_claim(self):
        rows = self.cycles()
        rows[1]['admittedInput'] = 1
        self.assertEqual(score(rows, False, 1, False), 'inconclusive')

    def test_background_password_ownership_invalidates_fix(self):
        rows = self.cycles()
        rows[0]['nativeWhileAway']['viewSecureOwner'] = 'true'
        self.assertEqual(score(rows, False, 1, True), 'inconclusive')

    def test_incomplete_activation_suite_is_not_a_pass(self):
        self.assertEqual(score(self.cycles()[:2], False, 1, False), 'inconclusive')

    def test_permissioned_images_cannot_be_replaced(self):
        for field in ['permissionApproved', 'permissionRequested', 'effectiveGrantConfirmed']:
            values = {key: False for key in ['permissionApproved', 'permissionRequested', 'effectiveGrantConfirmed']}
            values[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'consent image'):
                replaceable(values, {})

    def test_unknown_consent_state_cannot_be_replaced(self):
        with self.assertRaisesRegex(RuntimeError, 'consent image'):
            replaceable({}, {})

    def test_hide_uses_measured_state_and_preserves_false_api_result(self):
        row = {'status': 'observed', 'operationSucceeded': False, 'hidden': True,
               'inputPosted': False, 'hooksInstalled': False}
        manifest = SimpleNamespace(read_text=lambda: '{"activationHelperSHA256":"pinned"}')
        with patch.object(subject, 'MANIFEST', manifest), patch.object(subject, 'digest', return_value='pinned'), \
                patch.object(subject.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(row))):
            result = subject.activate(123, 'hide')
        self.assertFalse(result['operationSucceeded'])
        self.assertTrue(result['measuredEndStateReached'])

    def test_api_success_does_not_replace_missing_end_state(self):
        row = {'status': 'observed', 'operationSucceeded': True, 'hidden': False,
               'inputPosted': False, 'hooksInstalled': False}
        manifest = SimpleNamespace(read_text=lambda: '{"activationHelperSHA256":"pinned"}')
        with patch.object(subject, 'MANIFEST', manifest), patch.object(subject, 'digest', return_value='pinned'), \
                patch.object(subject.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(row))), \
                self.assertRaisesRegex(RuntimeError, 'did not complete'):
            subject.activate(123, 'hide')

    def test_physical_followup_requires_a_calibrated_engine_reference(self):
        value = {'status': 'native-route-reproduced', 'case': 'focus', 'targetStopped': True,
                 'sinkStopped': True, 'resumedNewActions': 1, 'cycles': self.cycles(1),
                 'engineIdentity': {'mappedFrameworks': {name: name for name in ['WebKit', 'WebCore', 'JavaScriptCore']}}}
        self.assertTrue(valid_reference(value))
        value['engineIdentity']['mappedFrameworks'].pop('WebCore')
        self.assertFalse(valid_reference(value))

    def test_a_failed_native_control_cannot_admit_a_physical_claim(self):
        self.assertFalse(valid_reference({'status': 'inconclusive', 'cycles': self.cycles(1)}))


if __name__ == '__main__':
    unittest.main()
