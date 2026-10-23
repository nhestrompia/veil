# Generated-input observation controls

The observation app accepted the fake action in all fifteen generated-input trials. No trial reported raw keyboard values. Seven trials reported no raw device values at all. The other trials included pointer or button reports whose physical source remains unverified.

| Generated route | Accepted fake action | No raw device values |
| --- | --- | --- |
| Session state | 3/3 | 0/3 |
| HID state | 3/3 | 0/3 |
| Private state | 3/3 | 1/3 |
| Curved HID trajectory | 3/3 | 3/3 |
| HID physical key codes | 3/3 | 3/3 |

These are observation controls. The app implements no input defense. Concurrent physical movement can explain mixed pointer records. The test did not establish physical inactivity, and the saved results preserve that limit.

The empty device streams show that successful synthetic app events need not produce device callbacks in these runs. A positive physical keyboard sample remains necessary. Absence alone cannot prove that the observer can receive physical keyboard input.

The [summary](evidence/hid-generated-results.json) records every trial. The full local observations remain in the ignored artifacts directory. They omit typed text, key codes, and device names. A physical sample and adaptive attacks are still required before any device gate can support a protection claim.

```sh
python3 tools/run_hid_observation.py --repetitions 3 --output artifacts/hid-synthetic-final
```
