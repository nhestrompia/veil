import os
from pathlib import Path
import subprocess
import unittest


READER = Path(__file__).resolve().parents[1] / ".build/renderer-metadata-read"


@unittest.skipUnless(READER.is_file(), "Build the metadata reader first")
class RendererMetadataReadTests(unittest.TestCase):
    def assert_refuses(self, arguments, expected):
        result = subprocess.run([str(READER), *arguments], capture_output=True, timeout=2)
        self.assertEqual(result.returncode, expected)
        self.assertEqual(result.stdout, b"")

    def test_missing_arguments(self):
        self.assert_refuses([], 64)

    def test_non_numeric_pid(self):
        self.assert_refuses(["invalid", "2", "3", "4"], 64)

    def test_protected_pid(self):
        self.assert_refuses(["1", "2", "3", "4"], 65)

    def test_unrelated_live_host(self):
        self.assert_refuses([str(os.getpid()), "2", "3", "4"], 66)


if __name__ == "__main__":
    unittest.main()
