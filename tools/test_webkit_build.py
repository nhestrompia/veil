import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_research_webkit as build


class ResearchEngineBuildTests(unittest.TestCase):
    def test_output_environment_bypasses_user_xcode_preferences(self):
        output = Path('/workspace/output')
        with patch.dict('os.environ', {'BUILD_WEBKIT_PRE_SCRIPT': '/unexpected/script'}):
            environment = build.build_environment(output)
        self.assertEqual(environment['WEBKIT_OUTPUTDIR'], str(output))
        self.assertEqual(environment['TMPDIR'], str(output / 'Temporary'))
        self.assertNotIn('BUILD_WEBKIT_PRE_SCRIPT', environment)

    def test_changed_source_is_refused_before_any_file_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'first').write_text('old')
            (source / 'second').write_text('unexpected')
            with patch.object(build, 'read_sources', return_value=({'revision': 'pinned'}, {'first': 'old', 'second': 'old'})), \
                 patch.object(build, 'revision_of', return_value='pinned'), \
                 patch.object(build, 'generate'), \
                 patch.object(build, 'changed_sources', return_value={'first': 'new', 'second': 'new'}):
                with self.assertRaisesRegex(RuntimeError, 'Refusing changed research source'):
                    build.stage(source)
            self.assertEqual((source / 'first').read_text(), 'old')

    def test_interrupted_old_and_new_mix_converges_to_exact_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'first').write_text('new')
            (source / 'second').write_text('old')
            patch_file = source / 'patch'
            patch_file.write_text('exact patch')
            with patch.object(build, 'read_sources', return_value=({'revision': 'pinned'}, {'first': 'old', 'second': 'old'})), \
                 patch.object(build, 'revision_of', return_value='pinned'), \
                 patch.object(build, 'generate'), \
                 patch.object(build, 'changed_sources', return_value={'first': 'new', 'second': 'new', 'header': 'new header'}), \
                 patch.object(build, 'BASE', source), patch.object(build, 'PATCH', patch_file):
                build.stage(source)
                build.stage(source)
            self.assertEqual((source / 'second').read_text(), 'new')
            self.assertEqual((source / 'header').read_text(), 'new header')
            self.assertFalse(json.loads((source / 'applied-source.json').read_text())['engineCompiled'])

    def test_line_ending_changes_are_refused_before_other_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'first').write_bytes(b'old\n')
            (source / 'second').write_bytes(b'old\r\n')
            with patch.object(build, 'read_sources', return_value=({'revision': 'pinned'}, {'first': 'old\n', 'second': 'old\n'})), \
                 patch.object(build, 'revision_of', return_value='pinned'), \
                 patch.object(build, 'generate'), \
                 patch.object(build, 'changed_sources', return_value={'first': 'new\n'}):
                with self.assertRaisesRegex(RuntimeError, 'Refusing changed research source'):
                    build.stage(source)
            self.assertEqual((source / 'first').read_bytes(), b'old\n')
