import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_engine_observation as subject
from run_engine_observation import score


class EngineObservationTests(unittest.TestCase):
    def test_disclosure_survives_failed_after_reference(self):
        self.assertEqual(score('capture', {'worked': True}, {'markerRecovered': True}, {}), 'bypass')

    def test_accepted_action_survives_failed_after_reference(self):
        self.assertEqual(score('ax-action', {}, {'newAcceptedActions': 1}, {}), 'bypass')

    def test_missing_capture_is_inconclusive_despite_good_references(self):
        self.assertEqual(score('capture', {'worked': True}, {'completed': False}, {'worked': True}), 'inconclusive')

    def test_empty_ocr_needs_completed_capture_and_both_references(self):
        self.assertEqual(score('capture', {'worked': True}, {'completed': True}, {'worked': True}),
                         'marker-not-recovered-in-bounded-observation')
        self.assertEqual(score('capture', {'worked': True}, {'completed': True}, {}), 'inconclusive')

    def test_successful_ax_api_requires_review_even_without_submission(self):
        self.assertEqual(score('ax-action', {'worked': True}, {'probe': {'setValueError': 0}}, {'worked': True}),
                         'partial-action-requires-review')

    def test_absent_controls_need_successful_matched_references(self):
        candidate = {'probe': {'error': 'Fixture field or action not found in AX tree'}}
        self.assertEqual(score('ax-action', {'worked': True}, candidate, {'worked': True}), 'no-action-observed')
        self.assertEqual(score('ax-action', {}, candidate, {'worked': True}), 'inconclusive')

    def test_candidate_exit_still_saves_bypass_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(subject, 'active', side_effect=RuntimeError('candidate exited')), \
                patch.object(subject, 'matching_pids', return_value=set()):
            output = Path(directory)
            report = {'status': 'bypass', 'rows': [{'verdict': 'bypass'}]}
            with self.assertRaisesRegex(RuntimeError, 'candidate exited'):
                subject.finish(report, {'pid': 42}, Mock(), Path('/probe'), output)
            saved = json.loads((output / 'results.json').read_text())
            self.assertEqual(saved['status'], 'bypass')
            self.assertEqual(saved['rows'], report['rows'])
            self.assertTrue(saved['probeStopped'])
            self.assertTrue(saved['referencesStopped'])


if __name__ == '__main__':
    unittest.main()
