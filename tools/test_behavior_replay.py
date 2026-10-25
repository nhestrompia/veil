import math
import unittest

from behavior_replay import features, motion


class BehaviorReplayTests(unittest.TestCase):
    def sample(self):
        return {"records": [{"origin": "app-event", "type": 5, "timestampSeconds": t,
                             "point": [x, y], "sourceState": 1}
                            for t, x, y in [(10, 100, 200), (10.1, 110, 200), (10.3, 115, 205)]]}

    def test_source_labels_and_absolute_position_do_not_enter_features(self):
        original = motion(self.sample())
        shifted = self.sample()
        for record in shifted["records"]:
            record.update(sourceState=-1, originPID=999, label="synthetic")
            record["point"][0] += 64
            record["point"][1] -= 32
        self.assertEqual(features(original), features(motion(shifted)))

    def test_recorded_behavior_can_be_copied_without_feature_change(self):
        points = motion(self.sample())
        self.assertEqual(features(points), features([tuple(row) for row in points]))

    def test_bad_timing_and_nonfinite_values_are_rejected(self):
        for value in [math.inf, math.nan, True, "10"]:
            sample = self.sample()
            sample["records"][1]["timestampSeconds"] = value
            with self.assertRaises(ValueError):
                motion(sample)
        sample = self.sample()
        sample["records"][1]["timestampSeconds"] = 9
        with self.assertRaises(ValueError):
            motion(sample)

    def test_keyboard_and_device_values_are_excluded(self):
        sample = self.sample()
        expected = features(motion(sample))
        sample["records"].extend([{"origin": "device-value", "category": "keyboard"},
                                  {"origin": "app-event", "type": 10}])
        self.assertEqual(expected, features(motion(sample)))


if __name__ == "__main__":
    unittest.main()
