"""Refuse false progress claims even when an actor reports success."""

from copy import deepcopy
import unittest

from run_renderer_progress_control import verify_progress


class ProgressAcceptanceTests(unittest.TestCase):
    def setUp(self):
        roles = ('host', 'content', 'gpu', 'network')
        records = {role: {'pid': 100 + index, 'path': role, 'startedSeconds': 10,
            'startedMicroseconds': 0, 'realUID': 501, 'effectiveUID': 501, 'savedUID': 501,
            'realGID': 20, 'effectiveGID': 20, 'savedGID': 20} for index, role in enumerate(roles)}
        self.ready = {'host': records['host'], 'servicesAfterSnapshot': {
            role: {'identity': records[role]} for role in roles[1:]},
            'progressBefore': {'nonce': 'document', 'ticks': 1}, 'javascript': {'nonce': 'document'},
            'readyMonotonicNanoseconds': 10, 'progressControl': True, 'javascriptPassed': True,
            'snapshotPassed': True, 'baselineSnapshotPassed': True, 'serviceIdentityStable': True}
        self.native = deepcopy(self.ready)
        self.native.update(progressAfter={'nonce': 'document', 'ticks': 5,
            'challenge': 'fresh', 'domChallenge': 'fresh'}, expectedChallenge='fresh',
            progressSampleStartedMonotonicNanoseconds=40, progressSampleFinishedMonotonicNanoseconds=50,
            servicesAfterProgress=deepcopy(self.ready['servicesAfterSnapshot']),
            completed=True, progressPassed=True, progressIdentityStable=True, visibleWindowCountAtEnd=0)
        self.actor = {'actorUID': 501, 'exitCode': 0, 'startedMonotonicNanoseconds': 20,
            'finishedMonotonicNanoseconds': 30, 'footer': [{'crossUser': False, 'passed': True,
                'recoveryComplete': True, 'watchdogReaped': True}], 'signals': [
                {'role': role, 'pid': records[role]['pid'], 'actorUID': 501, 'targetUID': 501,
                 'expectedOutcome': True, 'identityStable': True, 'notStoppedAfter': True,
                 'stopReturn': 0, 'observedStopped': True, 'continueReturn': 0} for role in roles]}

    def check(self):
        return verify_progress(self.ready, self.native, self.actor)['passed']

    def test_valid_ordered_progress(self):
        self.assertTrue(self.check())

    def test_a_sample_before_attack_completion_is_not_post_attack(self):
        self.native['progressSampleStartedMonotonicNanoseconds'] = 25
        self.assertFalse(self.check())

    def test_equal_timestamp_is_inconclusive(self):
        self.native['progressSampleStartedMonotonicNanoseconds'] = 30
        self.assertFalse(self.check())

    def test_frozen_timer_is_not_progress(self):
        self.native['progressAfter']['ticks'] = 1
        self.assertFalse(self.check())

    def test_another_document_is_not_progress(self):
        self.native['progressAfter']['nonce'] = 'replacement'
        self.assertFalse(self.check())

    def test_a_js_return_without_dom_change_is_not_completion(self):
        self.native['progressAfter']['domChallenge'] = 'old'
        self.assertFalse(self.check())

    def test_an_uncalibrated_pause_is_not_a_reference(self):
        self.actor['signals'][1]['observedStopped'] = False
        self.assertFalse(self.check())

    def test_replaced_role_is_not_stable(self):
        self.native['servicesAfterProgress']['gpu']['identity']['startedSeconds'] += 1
        self.assertFalse(self.check())

    def test_wrong_credentials_do_not_establish_isolation(self):
        self.native['servicesAfterProgress']['content']['identity']['savedUID'] = 0
        self.assertFalse(self.check())

    def test_failed_snapshot_is_not_a_redraw(self):
        self.native['snapshotPassed'] = False
        self.assertFalse(self.check())

    def test_omitted_role_is_not_success(self):
        self.actor['signals'].pop()
        self.assertFalse(self.check())

    def test_duplicate_role_is_not_success(self):
        self.actor['signals'][-1] = deepcopy(self.actor['signals'][0])
        self.assertFalse(self.check())

    def test_unreaped_watchdog_is_not_success(self):
        self.actor['footer'][0]['watchdogReaped'] = False
        self.assertFalse(self.check())


if __name__ == '__main__':
    unittest.main()
