# Native-input experiment findings

Milestone 2, October 23, 2026. This is a baseline shell experiment, not an agent-resistant MVP.

## Result

Permissioned CGEvent input operates the browser despite disabled inspection. The independent fixture accepted all 15 protected-browser trials across five working input adapters. The inspection-enabled control accepted the corresponding 15 trials. This rejects an agent-free claim for the current build.

| Route | Protected browser | Inspectable control |
| --- | --- | --- |
| Combined-session CGEvent source and Unicode input | 3/3 completed | 3/3 completed |
| HID-state CGEvent source and Unicode input | 3/3 completed | 3/3 completed |
| Private-state CGEvent source and Unicode input | 3/3 completed | 3/3 completed |
| Curved mouse trajectory with HID-state input | 3/3 completed | 3/3 completed |
| HID-state input with physical key codes | 3/3 completed | 3/3 completed |
| AX value setter and semantic button press | 0/3 completed, inconclusive | 0/3 completed, inconclusive |
| CGEvent posted directly to the app PID | 0/3 completed, inconclusive | 0/3 completed, inconclusive |

External AX reads recovered the fresh marker in all 21 trials for each browser. Input coordinates in the automated matrix came from AX. These are native observation-and-input attacks, not screenshot-only attacks or blind replay.

The AX-only action adapter returned successful API codes but submitted an empty field in both builds. The direct-PID adapter also failed to complete in both. Neither supplies evidence of a defensive block. Their control failures remain visible in the results.

A separate model-driven native computer-use trial recovered the marker, changed the field, and completed one protected-browser submission. That tool used accessibility observation and native interaction. It is a mixed route, not a claim that the standalone AX setter succeeded.

## Evidence and attribution

[Native matrix](evidence/native-input-results.json) contains all 42 trials, effective permissions, app binary hashes, attempted operations, submissions, and verdicts. [Computer-use evidence](evidence/native-computer-use.json) records the separate tool trial and oracle confirmation. Full local AX trees, fixture events, process logs, and controller observations remain under `artifacts/native-final/`.

The browser and probe are separate signed executables. The probe receives only the target PID and input plan. The Python controller alone queries the oracle. The fixture records HTTP submissions outside the browser. The loopback oracle is test instrumentation, not a boundary against unrestricted same-user code.

The exact probe binary reported Accessibility, event-posting, and Screen Recording access before the accepted matrix. Earlier runs with stale grants are retained locally and excluded. Rebuilding an ad hoc signed probe invalidated effective grants during development. A Settings switch alone did not establish permission. The accepted run uses the current binary and refreshed registrations.

## Reproduce

```sh
bash scripts/build.sh
bash scripts/build-probe.sh
python3 tools/fixture.py
```

Grant the current `dist/NativeProbe.app` Accessibility and Screen Recording access. Start the probe through Launch Services so its separate app identity owns the permission. After a rebuild, check effective access again. Grant changes require user approval.

```sh
python3 tools/run_native.py --repetitions 3 --output artifacts/native-repeat
python3 tools/verify_results.py artifacts/native-repeat/results.json
```

The verifier exits nonzero on disclosure, successful actions, or incomplete prevention evidence. The fixture and verifier tests pass. Both browser and probe builds compile with warnings treated as errors.

## Limits and next experiment

Three trials per adapter establish concrete bypasses, not population completion rates. There is no physical-human baseline, classifier evaluation, screen-reader usability result, or measured browser-attachment refusal yet. Curved movement is a generated attack baseline. It is not evidence of successful evasion of a trained detector.

Next, test ScreenCaptureKit, system screenshots, and a combined vision-and-input client. Keep browser protocol attachment separate from native computer-use access. A source-state filter needs an adaptive test because this probe can select HID state without physical input.
