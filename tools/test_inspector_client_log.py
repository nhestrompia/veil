import json
import subprocess
import unittest
from unittest.mock import patch

from inspector_client_log import classify, observe


class ClientLogTests(unittest.TestCase):
    def test_private_payloads_are_replaced_by_fixed_categories(self):
        rows = [
            {"subsystem": "com.apple.xpc", "eventMessage": "[0xabc] activating name=com.apple.webinspector.debugger"},
            {"subsystem": "com.apple.WebInspector", "eventMessage": "Created CURRENTMACHINE target: PRIVATE-HOST-MARKER"},
            {"subsystem": "com.apple.WebInspector", "eventMessage": "webinspectord validation failed"},
            {"subsystem": "com.apple.xpc", "eventMessage": "[0xabc] PRIVATE-PAYLOAD XPC_ERROR_CONNECTION_INTERRUPTED"},
            {"subsystem": "com.apple.xpc", "eventMessage": "[0xdef] unrelated PRIVATE-CONNECTION invalidated"},
        ]
        result = classify(rows)
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertFalse(result["rawMessagesSaved"])
        self.assertEqual([e["event"] for e in result["events"]], [
            "debugger-connection-activated", "current-machine-target-created",
            "webinspectord-validation-failed", "debugger-connection-interrupted"])

    def test_unrelated_endpoints_and_malformed_records_are_ignored(self):
        rows = [None, {"eventMessage": None},
                {"subsystem": "com.apple.xpc", "eventMessage": "[0xabc] name=com.apple.webinspector.debugger.other"},
                {"subsystem": "com.apple.xpc", "eventMessage": "[0xabc] invalidated"},
                {"subsystem": "unrelated", "eventMessage": "webinspectord validation failed"}]
        self.assertEqual(classify(rows)["events"], [])

    def test_observer_filters_exact_client_pid_and_executable(self):
        with patch("inspector_client_log.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "[]", "")) as run:
            result = observe(123)
        command = run.call_args.args[0]
        self.assertIn("processIdentifier == 123 AND processImagePath ==", command[-1])
        self.assertIn("/.build/inspector-discovery-control", command[-1])
        self.assertFalse(result["daemonLogsRead"])
        for pid in [True, 1, "123"]:
            with self.assertRaises(ValueError):
                observe(pid)

    def test_failed_or_malformed_log_response_saves_no_payload(self):
        for completed in [subprocess.CompletedProcess([], 1, "PRIVATE-STDOUT", "PRIVATE-STDERR"),
                          subprocess.CompletedProcess([], 0, "PRIVATE-INVALID-JSON", "")]:
            with patch("inspector_client_log.subprocess.run", return_value=completed):
                result = observe(123)
            self.assertNotIn("PRIVATE", json.dumps(result))
            self.assertIn(result["status"], ["unavailable", "invalid-response"])


if __name__ == "__main__":
    unittest.main()
