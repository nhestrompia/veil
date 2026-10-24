import signal
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch, call, Mock

import process_cleanup
from native_environment import require_input_safety


class ProcessCleanupTests(unittest.TestCase):
    def test_failed_readiness_stops_only_new_matching_processes(self):
        launcher = Mock(research_existing_pids={11})
        with patch.object(process_cleanup, "matching_pids", return_value={11, 22, 33}), patch.object(process_cleanup, "stop_owned", side_effect=[False, True]) as stop:
            self.assertFalse(process_cleanup.stop_launched(launcher, Path("/research/owned")))
            self.assertEqual({item.args[0] for item in stop.call_args_list}, {22, 33})

    def test_unrelated_process_is_not_stopped(self):
        with patch.object(process_cleanup, "process_matches", return_value=False), patch.object(process_cleanup.os, "kill") as kill:
            self.assertTrue(process_cleanup.stop_owned(12345, Path("/research/owned")))
            kill.assert_not_called()

    def test_waits_for_graceful_exit(self):
        with patch.object(process_cleanup, "process_matches", side_effect=[True, True, False]), patch.object(process_cleanup.os, "kill") as kill:
            self.assertTrue(process_cleanup.stop_owned(12345, Path("/research/owned")))
            kill.assert_called_once_with(12345, signal.SIGTERM)

    def test_stalled_owned_process_is_stopped_and_checked(self):
        with patch.object(process_cleanup, "process_matches", side_effect=[True, True, True, False]), patch.object(process_cleanup.time, "monotonic", side_effect=[0, 2, 3, 3.1]), patch.object(process_cleanup.os, "kill") as kill:
            self.assertTrue(process_cleanup.stop_owned(12345, Path("/research/owned")))
            self.assertEqual(kill.call_args_list, [call(12345, signal.SIGTERM), call(12345, signal.SIGKILL)])

    def test_reused_pid_never_receives_final_signal(self):
        with patch.object(process_cleanup, "process_matches", side_effect=[True, True, False]), patch.object(process_cleanup.time, "monotonic", side_effect=[0, 2]), patch.object(process_cleanup.os, "kill") as kill:
            self.assertTrue(process_cleanup.stop_owned(12345, Path("/research/owned")))
            kill.assert_called_once_with(12345, signal.SIGTERM)

    def test_failed_shutdown_is_reported(self):
        with patch.object(process_cleanup, "process_matches", return_value=True), patch.object(process_cleanup.time, "monotonic", side_effect=[0, 2, 3, 5]), patch.object(process_cleanup.os, "kill"):
            self.assertFalse(process_cleanup.stop_owned(12345, Path("/research/owned")))

    def test_zombie_is_already_stopped(self):
        result = subprocess.CompletedProcess([], 0, stdout="Z /research/owned\n")
        with patch.object(process_cleanup.subprocess, "run", return_value=result):
            self.assertFalse(process_cleanup.process_matches(12345, Path("/research/owned")))

    def test_input_preflight_fails_closed(self):
        for report in [{}, {"desktopInputSafety": {"available": False, "blockingMouseHookPIDs": []}},
                       {"desktopInputSafety": {"available": True, "blockingMouseHookPIDs": [12345]}}]:
            with self.subTest(report=report), self.assertRaises(RuntimeError):
                require_input_safety(report)
        require_input_safety({"desktopInputSafety": {"available": True, "blockingMouseHookPIDs": []}})


if __name__ == "__main__":
    unittest.main()
