import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from run_clock_channels import run
from run_engine_timer_attack import run as timer_attack
from run_native import Oracle


class ClockChannelControllerTests(unittest.TestCase):
    def test_invalid_clock_source_fails_before_starting_an_engine(self):
        with self.assertRaisesRegex(ValueError, "Unknown fixture clock source"):
            timer_attack(Path("unused"), Path("unused"), Path("unused"), clock_source="unknown")

    def test_controller_retains_failure_and_closes_the_owned_fixture(self):
        observed = {}

        def failed_trial(output, controller, engine_root, **options):
            oracle = Oracle(controller)
            trial = oracle.create()
            with urlopen(trial["url"] + "/clock") as response:
                self.assertGreater(json.load(response)["monotonicMS"], 0)
            self.assertEqual(controller.stat().st_mode & 0o777, 0o600)
            observed["url"] = trial["url"]
            raise RuntimeError("deliberate failed timing control")

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matrix"
            with patch("run_clock_channels.timer_attack", side_effect=failed_trial):
                with self.assertRaisesRegex(RuntimeError, "deliberate failed timing control"):
                    run(output, Path("unused"), ["server"], 1)
            report = json.loads((output / "results.json").read_text())
            self.assertTrue(report["fixtureShutdownVerified"])
            self.assertEqual(report["runs"][0]["status"], "inconclusive")
            self.assertIn("deliberate failed timing control", report["runs"][0]["error"])
            with self.assertRaises(OSError):
                urlopen(observed["url"], timeout=0.5)
