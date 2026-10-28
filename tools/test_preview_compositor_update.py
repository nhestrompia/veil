from pathlib import Path
import unittest

from build_preview_compositor_update import revised_source


class LayoutUpdateTests(unittest.TestCase):
    def test_only_three_reviewed_layout_lines_change(self):
        source = (Path(__file__).resolve().parent.parent / "Sources/Diagnostics/PreviewCompositorProbe.swift").read_text()
        updated = revised_source(source)
        changes = [(before, after) for before, after in zip(source.splitlines(), updated.splitlines()) if before != after]
        self.assertEqual(len(changes), 3)
        self.assertEqual(source.count("throw CompositorFailure"), updated.count("throw CompositorFailure"))
        self.assertIn("other.intersects(region)", updated)
        self.assertIn("PreviewCompositorBackdrop.level.rawValue", updated)
        self.assertIn("PreviewCompositorBackdrop.make(frame: backdropFrame)", updated)

    def test_changed_or_duplicate_seams_are_refused(self):
        source = (Path(__file__).resolve().parent.parent / "Sources/Diagnostics/PreviewCompositorProbe.swift").read_text()
        for changed in [source.replace("backdrop.level = .normal", "backdrop.level = .floating"), source + "\nbackdrop.level = .normal"]:
            with self.assertRaises(RuntimeError):
                revised_source(changed)


if __name__ == "__main__":
    unittest.main()
