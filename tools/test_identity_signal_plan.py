from pathlib import Path
import subprocess
import unittest

from prepare_identity_signal_run import stage_script


class IdentitySignalPlanTests(unittest.TestCase):
    def test_malformed_hash_cannot_become_administrator_shell_code(self):
        for digest in ["", "a" * 63, "a" * 65, "A" * 64, "a" * 63 + ";"]:
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                stage_script(Path("unused"), digest)

    def test_source_path_is_a_literal_shell_argument(self):
        path = Path("/tmp/research 'quoted' $(false)/control")
        script = stage_script(path, "a" * 64)
        self.assertIn("'\"'\"'", script)
        self.assertNotIn("eval ", script)
        # This checks shell syntax only. It does not execute the prepared commands.
        result = subprocess.run(["/bin/sh", "-n"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_plan_keeps_environment_and_exact_file_cleanup(self):
        script = stage_script(Path("/research/control"), "f" * 64)
        self.assertIn("/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C", script)
        self.assertIn('/bin/rm -f -- "$stage/identity-signal-control"', script)
        self.assertIn('/bin/rmdir -- "$stage"', script)
        self.assertNotIn("rm -rf", script)
        self.assertIn("--root-experiment", script)
        self.assertIn('"helperExitCode":%s', script)
        self.assertNotIn("launchctl", script)
        self.assertNotIn("dscl", script)

    def test_loader_constraints_repeat_after_the_staged_hash_check(self):
        script = stage_script(Path("/research/control"), "f" * 64)
        digest_check = script.index('if [ "$actual" != "$expected" ]')
        execution = script.index("--root-experiment")
        for operation in ["codesign --verify", "codesign -d", "otool -L", "otool -l", "LC_RPATH", "LC_DYLD_ENVIRONMENT"]:
            self.assertGreater(script.index(operation), digest_check)
            self.assertLess(script.index(operation), execution)
