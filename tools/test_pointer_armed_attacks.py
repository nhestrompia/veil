import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_pointer_armed_attacks as subject


class ArmedPointerRunnerTests(unittest.TestCase):
    def test_result_review_runs_in_both_approval_branches_without_posting_input(self):
        for retry, expected_count in [(False, 8), (True, 7)]:
            with self.subTest(reviewed_retry=retry), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                prior = root / 'artifacts/prior'
                prior.mkdir(parents=True)
                helper = root / '.build/ApprovedModifierPause'
                helper.parent.mkdir()
                helper.write_bytes(b'not an executable')
                routes = ['hid', 'session', 'private', 'curve-hid']
                save = lambda p, value: p.write_text(json.dumps(value))
                save(prior / 'results.json', {'restored': True, 'binarySHA256': 'same',
                     'results': [{'route': route, 'verdict': 'blocked', 'controlWorked': True,
                                  'repetition': 0} for route in routes]})
                for route in routes:
                    prefix = prior / f'0-{route}'
                    save(prefix.with_suffix('.control-ax.json'), {'elements': [
                        {'AXTitle': 'Record hardware click', 'position': [0, 0], 'size': [10, 10]}]})
                    save(prefix.with_suffix('.control-frame.json'), {'windows': [
                        {'kCGWindowLayer': 0, 'kCGWindowBounds': dict(X=0, Y=0, Width=100, Height=100)}]})
                for name in ['pause.log', 'restore.log']:
                    (prior / name).touch()
                if retry:
                    earlier = root / 'artifacts/hardware-pointer-154/armed-native-clicks'
                    earlier.mkdir(parents=True)
                    save(earlier / 'reviewed-assessment.json',
                         {'reviewedAssessment': 'inconclusive-physical-input-overlap'})
                    save(earlier / 'results.json', {'restored': True, 'binarySHA256': 'same',
                         'results': [{'route': 'hid', 'attempt': {'status': 'attempted'}}]})
                    for name in ['pause.log', 'restore.log']:
                        (earlier / name).touch()
                log = root / 'browser.log'
                log.write_text('HARDWARE_POINTER armed=true\n')
                session = root / 'session.json'
                save(session, {'pid': 123, 'binarySHA256': 'same', 'log': str(log),
                               'controller': 'unused', 'trial': {'id': 'same'}})
                plan = root / 'plan.json'
                save(plan, {'approved': True, 'executed': True, 'output': str(prior),
                            'sessionFile': str(session), 'repetitions': 3, 'maximumSeconds': 240,
                            'pauseHelperSHA256': hashlib.sha256(helper.read_bytes()).hexdigest()})
                initial = {'id': 'same', 'events': [], 'submissions': []}
                loaded = {**initial, 'submissions': [{'accepted': True}]}
                oracle = Mock()
                oracle.state.side_effect = [initial] + [loaded] * 100

                def fake_probe(arguments, *args, **kwargs):
                    if arguments == ['permissions']:
                        return {'postEvents': True}
                    with log.open('a') as stream:
                        stream.write('INPUT_QUEUE_REFUSED type=1\n')
                    return {'status': 'attempted'}

                def fake_subprocess(arguments, **kwargs):
                    if arguments[1] == 'pause':
                        Path(arguments[2]).write_text('{}')

                with patch.object(subject, 'ROOT', root), patch.object(subject.os, 'getuid', return_value=501), \
                        patch.object(subject, 'active'), patch.object(subject, 'Oracle', return_value=oracle), \
                        patch.object(subject, 'require_input_safety'), \
                        patch.object(subject, 'matching_pids', return_value=set()), \
                        patch.object(subject, 'frame'), patch.object(subject, 'translated_point', return_value=[0, 0]), \
                        patch.object(subject, 'probe', side_effect=fake_probe), \
                        patch.object(subject.subprocess, 'run', side_effect=fake_subprocess), \
                        patch.object(subject.time, 'sleep'), \
                        patch.object(subject.time, 'monotonic', side_effect=range(0, 1000, 11)), \
                        patch.object(subject.signal, 'signal'), patch.object(subject.signal, 'alarm'):
                    result = subject.run(plan, root / 'artifacts/output', reviewed_retry=retry)
                self.assertTrue(result['restored'])
                self.assertEqual(len(result['results']), expected_count)
                self.assertTrue(all(row['verdict'] == 'blocked' for row in result['results']))


if __name__ == '__main__':
    unittest.main()
