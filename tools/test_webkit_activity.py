import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import prepare_webkit_activity as activity


class PinnedActivitySourceTests(unittest.TestCase):
    def manifest(self, root):
        manifest = root / "manifest.json"
        data = b"pinned source"
        manifest.write_text(json.dumps({"revision": "fixed", "files": [{"path": "source.h",
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "url": "https://example.invalid/fixed/source.h"}]}))
        return manifest, data

    def test_fetch_never_overwrites_a_modified_cached_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = self.manifest(root)
            source = root / "source.h"
            source.write_bytes(b"modified")
            with patch.object(activity, "MANIFEST", manifest), patch.object(activity.urllib.request, "urlopen") as fetch:
                with self.assertRaisesRegex(RuntimeError, "Pinned source changed"):
                    activity.read_sources(root, fetch=True)
            fetch.assert_not_called()
            self.assertEqual(source.read_bytes(), b"modified")

    def test_bad_download_is_not_written_to_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, data = self.manifest(root)
            response = MagicMock()
            response.__enter__.return_value.read.return_value = b"x" * len(data)
            with patch.object(activity, "MANIFEST", manifest), patch.object(activity.urllib.request, "urlopen", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "Downloaded source identity mismatch"):
                    activity.read_sources(root, fetch=True)
            self.assertFalse((root / "source.h").exists())
