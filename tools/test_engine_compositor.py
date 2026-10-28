import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_engine_compositor as subject


class EngineCompositorTests(unittest.TestCase):
    def record(self, approved):
        return Mock(read_text=lambda: json.dumps({'path': str(subject.APP), 'executableSHA256': 'pinned',
                                                'sourceHashes': {}, 'permissionApproved': approved}))

    def test_new_recorder_cannot_capture_without_approval(self):
        with patch.object(subject, 'MANIFEST', self.record(False)), \
                patch.object(subject, 'digest', return_value='pinned'), \
                patch.object(subject.subprocess, 'Popen') as launch, \
                self.assertRaisesRegex(RuntimeError, 'approval'):
            subject.invoke(['sequence', 42, 43], subject.ROOT / 'artifacts/unused.json')
        launch.assert_not_called()

    def test_runner_has_no_permission_request_command(self):
        with patch.object(subject, 'MANIFEST', self.record(True)), \
                patch.object(subject, 'digest', return_value='pinned'), \
                patch.object(subject.subprocess, 'Popen') as launch, \
                self.assertRaises(ValueError):
            subject.invoke(['request-screen-recording'], subject.ROOT / 'artifacts/unused.json')
        launch.assert_not_called()

    def test_partial_recording_still_reports_a_disclosed_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'candidate'
            image = Path(directory) / 'partial.png'
            image.write_bytes(b'fake image for mocked OCR')
            later = Path(directory) / 'later.png'
            later.write_bytes(b'fake image for mocked OCR')
            oracle = Mock()
            oracle.state.return_value = {'secret': 'AFB-1234ABCD'}
            windows = {'windows': [{'kCGWindowOwnerPID': 42, 'kCGWindowLayer': 0,
                                   'kCGWindowAlpha': 1, 'kCGWindowBounds': {'Width': 1000, 'Height': 772},
                                   'kCGWindowNumber': 43}]}
            partial = {'status': 'refused', 'images': [str(image), str(later)], 'error': 'coverage lost'}
            with patch.object(subject, 'activate'), \
                    patch.object(subject, 'invoke', return_value=partial), \
                    patch.object(subject, 'probe', side_effect=[windows, {'text': [{'text': 'AFB-1234ABCD'}]},
                                                              RuntimeError('later OCR failed')]):
                result = subject.capture({'pid': 42, 'trial': {'id': 'fake'}}, prefix, oracle)
            self.assertTrue(result['markerRecovered'])
            self.assertFalse(subject.fully_audited(result))
            self.assertTrue(result['markerChecks'])
            saved = json.loads(prefix.with_suffix('.json').read_text())
            self.assertTrue(saved['markerRecovered'])
            self.assertEqual(saved['markerChecks'][-1]['error'], 'later OCR failed')


if __name__ == '__main__':
    unittest.main()
