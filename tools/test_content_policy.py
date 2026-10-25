import unittest

from run_content_policy import export_restricted, interfaces_restricted


class ContentPolicyTests(unittest.TestCase):
    def test_missing_reference_interfaces_cannot_count_as_restricted(self):
        row = {"status": "observed", "policyAccepted": True, "effectiveConfigurationRestricted": True,
               "unknownFeatureRefused": True, "controlPage": {"interfaces": {"secure": True}},
               "restrictedPage": {"interfaces": {"secure": True, "share": "undefined", "clipboard": "undefined", "publicKey": "undefined"}}}
        self.assertFalse(interfaces_restricted(row))
        row["controlPage"]["interfaces"].update(share="function", clipboard="object", publicKey="function")
        self.assertTrue(interfaces_restricted(row))

    def test_native_success_code_without_reference_marker_is_inconclusive(self):
        row = {"controlPage": {"selectionWriteAccepted": True}, "restrictedPage": {
            "selectionHasMarker": True, "selectionWriteAccepted": False, "namedPasteboardUnchanged": True}}
        self.assertFalse(export_restricted(row))
