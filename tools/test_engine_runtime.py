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
        text = '__TEXT 100000000-100001000 [4K] r-x/rwx SM=COW /System/Library/Frameworks/WebKit.framework/Versions/A/WebKit'
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

    def test_vmmap_permissions_are_not_part_of_a_framework_path(self):
        root = Path('/workspace/build with spaces')
        text = '\n'.join(f'__TEXT 100000000-100001000 [4K] r-x/rwx SM=COW          {root}/{name}.framework/Versions/A/{name}'
                         for name in engine.REQUIRED)
        found = engine.mapped_frameworks(text, root)
        self.assertEqual(found, {name: str(root / f'{name}.framework/Versions/A/{name}') for name in engine.REQUIRED})

    def test_unused_shared_cache_fragments_do_not_claim_a_loaded_image(self):
        root = Path('/workspace/build')
        loaded = '\n'.join(f'__TEXT 100000000-100001000 [4K] r-x/rwx SM=COW {root}/{name}.framework/Versions/A/{name}'
                           for name in engine.REQUIRED)
        unused = 'unused __DATA 1f5933600-1f5934000 [2560] rw-/rw- SM=COW on dirty page unused /System/Library/Frameworks/WebKit.framework/Versions/A/Frameworks/WebCore.framework/Versions/A/WebCore'
        self.assertEqual(set(engine.mapped_frameworks(loaded + '\n' + unused, root)), engine.REQUIRED)

    def test_unused_expected_images_cannot_satisfy_identity(self):
        root = Path('/workspace/build')
        unused = '\n'.join(f'unused __DATA 100000000-100001000 [4K] rw-/rw- SM=COW on dirty page unused {root}/{name}.framework/Versions/A/{name}'
                           for name in engine.REQUIRED)
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            engine.mapped_frameworks(unused, root)
