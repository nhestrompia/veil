import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from prepare_renderer_identity_run import APP, SUPERVISOR, bounded_tool, copy_program, prepare, stage_script


class RendererIdentityStageTests(unittest.TestCase):
    def setUp(self):
        self.stage = Path(subprocess.run(["/usr/bin/mktemp", "-d", "/private/tmp/agentfreebrowser-renderer.XXXXXX"],
                                         capture_output=True, text=True, check=True).stdout.strip())
        self.stage.chmod(0o700)
        self.source_dir = Path(tempfile.mkdtemp(prefix="afb-source-", dir="/private/tmp"))
        self.addCleanup(shutil.rmtree, self.stage)
        self.addCleanup(shutil.rmtree, self.source_dir)
        self.source = self.source_dir / "input"
        self.source.write_bytes(b"fixed-test-code")
        self.source.chmod(0o600)

    def copy(self, source=None, size=15):
        manifest = [{"source": str(source or self.source), "staged": "output", "size": size}]
        script = copy_program(manifest, os.getuid(), stage_uid=os.getuid())
        return subprocess.run(["/usr/bin/perl", "-T", "-e", script, str(self.stage)],
                              capture_output=True, timeout=3)

    def test_regular_exact_copy(self):
        result = self.copy()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.stage / "output").read_bytes(), b"fixed-test-code")

    def test_symlink_source_refuses(self):
        link = self.source_dir / "link"
        link.symlink_to(self.source)
        self.assertNotEqual(self.copy(link).returncode, 0)
        self.assertFalse((self.stage / "output").exists())

    def test_fifo_source_refuses_without_blocking(self):
        fifo = self.source_dir / "fifo"
        os.mkfifo(fifo, 0o600)
        self.assertNotEqual(self.copy(fifo).returncode, 0)
        self.assertFalse((self.stage / "output").exists())

    def test_shared_write_source_refuses(self):
        self.source.chmod(0o666)
        self.assertNotEqual(self.copy().returncode, 0)

    def test_hardlink_source_refuses(self):
        os.link(self.source, self.source_dir / "hardlink")
        self.assertNotEqual(self.copy().returncode, 0)

    def test_size_mismatch_refuses(self):
        self.assertNotEqual(self.copy(size=16).returncode, 0)

    def test_destination_symlink_refuses(self):
        target = self.source_dir / "untouched"
        target.write_bytes(b"unchanged")
        (self.stage / "output").symlink_to(target)
        self.assertNotEqual(self.copy().returncode, 0)
        self.assertEqual(target.read_bytes(), b"unchanged")

    def test_stage_modes_refuse(self):
        self.stage.chmod(0o755)
        self.assertNotEqual(self.copy().returncode, 0)

    def test_script_seals_only_after_hash_and_signature_checks(self):
        manifest = [{"source": str(self.source), "staged": "renderer-identity-supervisor", "size": 15,
                     "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest()}]
        script = stage_script(manifest, os.getuid(), {"renderer-identity-supervisor": ["/usr/lib/libSystem.B.dylib"]})
        self.assertLess(script.index("shasum"), script.index("/bin/chmod 0711"))
        self.assertLess(script.index("--verify"), script.index("--root-smoke"))
        self.assertNotIn("/bin/cp", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("launchctl", script)

    @unittest.skipUnless(SUPERVISOR.exists() and APP.exists(), "Build the separate renderer diagnostic first")
    def test_partial_library_output_with_failure_stops_before_helper(self):
        plan = prepare(self.source_dir / "plan.json")

        def failing_library_tool(command, arguments):
            if command == "/usr/bin/otool" and arguments[0] == "-L":
                # Correct-looking partial output must never hide the tool's failure.
                return "/usr/bin/printf 'image:\\n/usr/lib/libSystem.B.dylib\\n'; exit 73"
            return bounded_tool(command, arguments)

        with patch("prepare_renderer_identity_run.bounded_tool", side_effect=failing_library_tool):
            script = stage_script(plan["manifest"], os.getuid(), plan["libraries"], stage_uid=os.getuid())
        run = subprocess.run(["/usr/bin/env", "-i", "PATH=/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL=C",
                              "/bin/sh", "-c", script], capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 73, run.stderr)
        self.assertNotIn(b"STAGING_RESULT", run.stdout)
        self.assertNotIn(b"SUPERVISOR_READY", run.stdout)


if __name__ == "__main__":
    unittest.main()
