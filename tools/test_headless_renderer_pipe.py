import subprocess
import sys
import unittest

from run_headless_renderer_probe import collect_stdout


class HeadlessRendererPipeTests(unittest.TestCase):
    def child(self, script):
        process = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE)
        self.addCleanup(self.stop_child, process)
        return process

    @staticmethod
    def stop_child(process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        process.stdout.close()

    def test_exact_limit_and_exit(self):
        process = self.child("import os;os.write(1,b'x'*1024)")
        self.assertEqual(collect_stdout(process, limit=1024, timeout=3), b"x" * 1024)

    def test_oversized_stream_refuses_before_eof(self):
        process = self.child("import os,time;os.write(1,b'x'*4096);time.sleep(10)")
        with self.assertRaisesRegex(RuntimeError, "exceeds"):
            collect_stdout(process, limit=1024, timeout=3)

    def test_silent_stream_hits_deadline(self):
        process = self.child("import time;time.sleep(10)")
        with self.assertRaises(subprocess.TimeoutExpired):
            collect_stdout(process, timeout=0.1)

    def test_eof_without_exit_hits_deadline(self):
        process = self.child("import os,time;os.close(1);time.sleep(10)")
        with self.assertRaises(subprocess.TimeoutExpired):
            collect_stdout(process, timeout=0.1)


if __name__ == "__main__":
    unittest.main()
