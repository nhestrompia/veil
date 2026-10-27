"""Regression for a readable stream marker misclassified after Vision OCR."""

import unittest

from run_pixel_agent_audit import marker_recovery


class MarkerRecoveryTests(unittest.TestCase):
    def test_recorded_clear_stream_glyphs(self):
        ocr = {'text': [{'text': 'Disclosure marker: AFB-ЕСОBЗ33A'}]}
        result = marker_recovery(ocr, 'AFB-EC0B333A')
        self.assertFalse(result['exact'])
        self.assertTrue(result['visualHexAliases'])

    def test_different_marker_is_not_recovered(self):
        result = marker_recovery({'text': [{'text': 'AFB-ЕСОBЗ33A'}]}, 'AFB-EC0B333B')
        self.assertFalse(any(result.values()))

    def test_empty_black_frame_has_no_marker(self):
        self.assertFalse(any(marker_recovery({'text': []}, 'AFB-EC0B333A').values()))


if __name__ == '__main__':
    unittest.main()
