import unittest

from pointer_attempt_review import review


class PointerAttemptReviewTests(unittest.TestCase):
    def test_off_target_click_is_not_a_block_even_without_task_completion(self):
        before = {'id': 'same', 'events': [], 'submissions': [{'accepted': True}]}
        after = {**before, 'events': [
            {'type': 'pointerdown', 'x': 457, 'y': 298},
            {'type': 'pointerup', 'x': 457, 'y': 298},
            {'type': 'click', 'x': 457, 'y': 298}]}
        result = review(before, after, 'INPUT_GATE_ACCEPTED type=1\nINPUT_GATE_ACCEPTED type=2\n')
        self.assertEqual(result['outcome'], 'input-observed-without-task-action')
        self.assertEqual(result['newAcceptedTaskActions'], 0)
        self.assertEqual(result['acceptedNativeEvents'], 2)
        self.assertEqual(len(result['newPageInputEvents']), 3)
        self.assertFalse(result['attributionEstablished'])

    def test_admitted_event_without_dom_receipt_is_still_observed(self):
        state = {'id': 'same', 'events': [], 'submissions': []}
        self.assertEqual(review(state, state, 'INPUT_GATE_ACCEPTED type=1')['outcome'],
                         'input-observed-without-task-action')

    def test_unchanged_fixture_and_refused_input_are_not_interaction(self):
        state = {'id': 'same', 'events': [{'type': 'page-ready'}], 'submissions': []}
        self.assertEqual(review(state, state, 'INPUT_QUEUE_REFUSED type=1')['outcome'],
                         'no-observed-interaction')

    def test_new_action_is_recorded_separately_from_origin(self):
        before = {'id': 'same', 'events': [], 'submissions': []}
        after = {**before, 'submissions': [{'accepted': True}]}
        result = review(before, after, '')
        self.assertEqual(result['outcome'], 'task-action-observed')
        self.assertEqual(result['inputOrigin'], 'unresolved')

    def test_replaced_or_saturated_history_is_inconclusive(self):
        before = {'id': 'same', 'events': [{'type': 'page-ready'}], 'submissions': []}
        for events in [[], [{'type': 'page-ready'}] * 5000]:
            self.assertEqual(review(before, {**before, 'events': events}, '')['outcome'],
                             'inconclusive-fixture-history')

    def test_different_trials_cannot_be_compared(self):
        with self.assertRaises(ValueError):
            review({'id': 'one'}, {'id': 'two'}, '')


if __name__ == '__main__':
    unittest.main()
