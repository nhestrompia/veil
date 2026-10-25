from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from prepare_webkit_source import git_environment, require_disk, terminate_group


class WebKitSourceSafetyTests(unittest.TestCase):
    def test_dependency_git_does_not_inherit_the_parent_repository(self):
        with patch.dict('os.environ', {"GIT_DIR": "/parent/repository", "GIT_INDEX_FILE": "/parent/index"}):
            environment = git_environment()
        self.assertNotIn("GIT_DIR", environment)
        self.assertNotIn("GIT_INDEX_FILE", environment)
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_refuses_when_the_disk_reserve_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('prepare_webkit_source.shutil.disk_usage') as usage:
                usage.return_value.free = 0
                with self.assertRaisesRegex(RuntimeError, "disk reserve"):
                    require_disk(Path(directory))

    def test_cleanup_stops_only_the_process_group_it_started(self):
        command = [sys.executable, '-c', 'import time; time.sleep(30)']
        managed = subprocess.Popen(command, start_new_session=True)
        unrelated = subprocess.Popen(command, start_new_session=True)
        try:
            terminate_group(managed)
            self.assertIsNotNone(managed.poll())
            self.assertIsNone(unrelated.poll())
        finally:
            terminate_group(managed)
            terminate_group(unrelated)
