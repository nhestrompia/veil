from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import engine_runtime as engine


class EngineIdentityTests(unittest.TestCase):
    def test_incomplete_build_refuses_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'build-results.json').write_text('{"engineCompiled":false}')
            (base / 'applied-source.json').write_text('{}')
            with patch.object(engine, 'BASE', base):
                with self.assertRaisesRegex(RuntimeError, 'did not finish'):
                    engine.engine_environment(base / 'output/Release')

    def test_system_framework_cannot_satisfy_the_mapping_check(self):
        text = 'mapped /System/Library/Frameworks/WebKit.framework/Versions/A/WebKit'
        with self.assertRaisesRegex(RuntimeError, 'unexpected framework'):
            engine.mapped_frameworks(text, Path('/workspace/build'))

    def test_missing_content_framework_refuses_identity(self):
        text = 'mapped /workspace/build/WebKit.framework/Versions/A/WebKit'
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            engine.mapped_frameworks(text, Path('/workspace/build'))

    def test_all_three_exact_mapped_images_pass(self):
        text = '\n'.join(f'mapped /workspace/build/{name}.framework/Versions/A/{name}'
                         for name in engine.REQUIRED)
        self.assertEqual(set(engine.mapped_frameworks(text, Path('/workspace/build'))), engine.REQUIRED)
