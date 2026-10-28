import copy
import unittest

from run_preview_renderer_reads import read_worked, validate_physical


class PreviewRendererReadTests(unittest.TestCase):
    def test_physical_declaration_requires_exact_session(self):
        session = {"pid": 123, "binarySHA256": "pinned"}
        physical = {"operatorDeclaresPhysicalCompletion": True, "pid": 123,
                    "binarySHA256": "pinned", "deviceBound": True, "acceptedSubmissions": 1}
        validate_physical(session, physical)
        for key, value in [("pid", 124), ("binarySHA256", "changed"),
                           ("operatorDeclaresPhysicalCompletion", False), ("deviceBound", False),
                           ("acceptedSubmissions", 0)]:
            changed = {**physical, key: value}
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                validate_physical(session, changed)

    def test_host_marker_does_not_calibrate_renderer_read(self):
        row = {"status": "observed", "accessibilityQueried": True, "cleanupVerified": True,
               "queries": [{"kind": "host", "researchMarkers": ["AFB-0123ABCD"]}]}
        self.assertFalse(read_worked(row, "AFB-0123ABCD"))
        row["queries"][0]["kind"] = "renderer"
        self.assertTrue(read_worked(row, "AFB-0123ABCD"))
        self.assertFalse(read_worked(row, "AFB-FFFFFFFF"))

    def test_permission_or_cleanup_failure_does_not_calibrate(self):
        row = {"status": "observed", "accessibilityQueried": True, "cleanupVerified": True,
               "queries": [{"kind": "renderer", "researchMarkers": ["AFB-0123ABCD"]}]}
        for key, value in [("status", "inconclusive"), ("accessibilityQueried", False), ("cleanupVerified", False)]:
            changed = copy.deepcopy(row)
            changed[key] = value
            with self.subTest(key=key):
                self.assertFalse(read_worked(changed, "AFB-0123ABCD"))
