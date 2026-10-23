import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

import run_native


class ProbeLifecycleTests(unittest.TestCase):
    def test_timeout_stops_verified_helper_before_propagating(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "attempt.json"
            pid_file = root / "attempt.json.pid"
            pid_file.write_text("99999")
            binary = root / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"

            def launch_or_inspect(arguments, **_):
                if arguments[0] == "open":
                    self.assertFalse(pid_file.exists(), "Discard stale PID records before launch")
                    pid_file.write_text("12345")
                    raise subprocess.TimeoutExpired(arguments, 40)
                self.assertEqual(arguments, ["ps", "-p", "12345", "-o", "comm="])
                return subprocess.CompletedProcess(arguments, 0, stdout=str(binary), stderr="")

            with patch.object(run_native, "ROOT", root), patch.object(run_native.subprocess, "run", side_effect=launch_or_inspect), patch.object(run_native.os, "kill", side_effect=[None, ProcessLookupError()]) as kill:
                with self.assertRaises(subprocess.TimeoutExpired):
                    run_native.probe(["permissions"], output)
                self.assertEqual(kill.call_args_list, [call(12345, signal.SIGTERM), call(12345, 0)])

    def test_unrelated_process_is_never_stopped(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "probe.pid"
            pid_file.write_text("12345")
            with patch.object(run_native.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="/unrelated/app", stderr="")), patch.object(run_native.os, "kill") as kill:
                run_native.stop_timed_out_probe(pid_file)
                kill.assert_not_called()

    def test_missing_or_invalid_pid_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "probe.pid"
            with patch.object(run_native.subprocess, "run") as process, patch.object(run_native.os, "kill") as kill:
                run_native.stop_timed_out_probe(pid_file)
                for value in ["invalid", "0", "-1"]:
                    pid_file.write_text(value)
                    run_native.stop_timed_out_probe(pid_file)
                process.assert_not_called()
                kill.assert_not_called()

    def test_stalled_verified_helper_receives_final_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "probe.pid"
            pid_file.write_text("12345")
            binary = run_native.ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
            with patch.object(run_native.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout=str(binary), stderr="")) as process, patch.object(run_native.time, "monotonic", side_effect=[0, 2]), patch.object(run_native.os, "kill") as kill:
                run_native.stop_timed_out_probe(pid_file)
                self.assertEqual(process.call_count, 2)
                self.assertEqual(kill.call_args_list, [call(12345, signal.SIGTERM), call(12345, signal.SIGKILL)])

    def test_reused_pid_does_not_receive_final_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "probe.pid"
            pid_file.write_text("12345")
            binary = run_native.ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
            matches = [subprocess.CompletedProcess([], 0, stdout=str(binary), stderr=""),
                       subprocess.CompletedProcess([], 0, stdout="/unrelated/replacement", stderr="")]
            with patch.object(run_native.subprocess, "run", side_effect=matches), patch.object(run_native.time, "monotonic", side_effect=[0, 2]), patch.object(run_native.os, "kill") as kill:
                run_native.stop_timed_out_probe(pid_file)
                self.assertEqual(kill.call_args_list, [call(12345, signal.SIGTERM)])


if __name__ == "__main__":
    unittest.main()
