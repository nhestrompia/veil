import unittest

from verify_results import assess


class VerifierTests(unittest.TestCase):
    def test_bypass_wins_over_other_tool_errors(self):
        self.assertEqual("failed", assess([{"verdict": "inconclusive"}, {"verdict": "bypass"}])[0])

    def test_disclosure_fails_even_without_action(self):
        self.assertEqual("failed", assess([{"verdict": "inconclusive", "disclosure": True}])[0])

    def test_unavailable_or_empty_evidence_cannot_pass(self):
        self.assertEqual("inconclusive", assess([])[0])
        self.assertEqual("inconclusive", assess([{"verdict": "inconclusive"}])[0])
        self.assertEqual("inconclusive", assess([{"verdict": "blocked"}])[0])

    def test_explicit_blocks_require_controls(self):
        self.assertEqual("passed", assess([{"verdict": "blocked", "controlWorked": True}])[0])


if __name__ == "__main__":
    unittest.main()
