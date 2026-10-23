# Source-state filter experiment

Milestone 4, October 23, 2026. The source-state filter is an isolated research variant. It is not enabled in the default browser.

## Hypothesis and implementation

The candidate admits mouse-down, key-down, and scroll events only when their CGEvent source state is HID. It refuses other source states before dispatch to WKWebView. The app logs acceptance or refusal with event type and source state. It does not log typed content.

The experiment asks whether that rule rejects the known input client. It does not assume that HID state proves a physical person acted. `dist/MetadataExperiment.app` has its own bundle identity and a visible experimental status.

## Paired results

Each route ran three fresh sessions against the normal shell and the candidate. Both builds used the same fixture and independent submission oracle.

| Agent route | Baseline actions completed | Filter actions completed |
| --- | --- | --- |
| Session-state CGEvent input | 3/3 | 0/3, explicit refusal |
| Generated HID-state input | 3/3 | 3/3 |
| Curved HID-state trajectory | 3/3 | 3/3 |
| HID-state input with key codes | 3/3 | 3/3 |

The adapted client changed its event source to HID. The app's own logs recorded source state `1` on the synthetic events it accepted. All nine adapted trials completed. The detector's three basic-client refusals therefore do not establish human origin or general input prevention.

A separate screenshot/OCR/HID-input client completed 3/3 filter trials without an AX tree or DOM access. Both capture methods recovered the fresh marker in all three. The native AX observer also recovered the marker in every paired native trial.

See [native evidence](evidence/metadata-input-results.json) and [vision evidence](evidence/metadata-vision-results.json). The native evidence includes target hashes, paired control outcomes, app event-log samples, and accepted or refused event counts. Local raw logs and fixture events remain under `artifacts/metadata-native/` and `artifacts/metadata-vision/`.

## Decision

Reject source state alone as the input-protection mechanism. Keep the variant as a reproducible negative experiment. Do not enable it by default or describe HID events as physical human input.

No trained behavioral detector was tested. The curved trajectory generator and fixture event capture supply synthetic baselines for the separate mouse-behavior track. There is no physical-human dataset or measured false-block rate. Human trajectory collection, participant-separated evaluation, trace replay, and adaptive classifier attacks remain necessary before a behavioral claim.

The current implementation is a research browser and attack testbed. Its native and vision bypasses fail the agent-free gate. The completed experiments also do not yet establish the useful end-to-end resistance required for an agent-resistant MVP. A Chromium fork is not justified by these results alone.

## Reproduce

```sh
bash scripts/build.sh
python3 tools/run_native.py --targets AgentFreeBrowser MetadataExperiment --routes session hid curve-hid keycodes-hid --repetitions 3 --output artifacts/metadata-repeat
python3 tools/run_capture.py --targets MetadataExperiment --repetitions 3 --output artifacts/metadata-vision-repeat
python3 tools/verify_results.py artifacts/metadata-repeat/results.json
```

Keep the existing, permissioned probe binary unchanged unless its source needs rebuilding. Its grants do not transfer automatically to a rebuilt ad hoc signature. A failed grant or control is inconclusive, not a defensive success.
