# Foreground input and exposure experiments

Both policies fail the agent-free goal. Secure Event Input accepts synthetic actions while its mode is active. The reduced-exposure build still exposes content and semantic actions through Accessibility, or AX.

## Secure Event Input

`SecureInputExperiment.app` enables the mode while active and releases its own request before deactivation or termination. The experiment follows the same website path as the inspection-positive control. Apple documents this API as an interception defense for sensitive entry. It does not promise input-origin authentication. See the [API research](research/remaining-boundaries.md).

| Attack | Experiment completed | Control completed |
| --- | --- | --- |
| HID-state Unicode events | 3/3 | 3/3 |
| HID-state physical key codes | 3/3 | 3/3 |
| Window capture, OCR, and native input | 3/3 | 3/3 |

HID means Human Interface Device. The first two attacks generated events through CGEvent. They did not use physical devices. `SecureInputWindow` recorded the effective mode at delivery. Across six native trials, all 84 logged pointer or keyboard events arrived with the mode enabled. No logged event reported the mode disabled. The fixture independently recorded accepted actions.

The [verified native results](evidence/secure-event-results.json) include event counts and target hashes. The [initial vision results](evidence/foreground-vision-results.json) include the screenshot-driven comparison. The earlier failed-control runs remain inconclusive. The [route calibration](route-calibration.md) explains the corrected preflight.

## Reduced exposure

`ReducedExposureExperiment.app` adds `WKWebView.setAccessibilityHidden(true)` and `NSWindow.sharingType = .none`. It also enables Secure Event Input. These settings do not establish an access boundary for every AX method.

The updated probe follows explicit window and focused-element attributes as well as child elements. It recovered fresh page markers in all three reduced-exposure semantic-action trials. It then focused the field, set the fake value, and invoked the button through AX. It used no CGEvent input for that route.

| Attack | Experiment completed | Control completed |
| --- | --- | --- |
| AX focus, value setter, and semantic button | 3/3 | 3/3 |
| Input at the known fixture location | 2/3 | 3/3 |

The known-layout agent learned field coordinates from the separate control. It used no target coordinates or target screenshot to place its input. A separate AX observation still recovered the marker. One trial remained inconclusive, so the report preserves 2/3 rather than calling it a complete pass rate.

The [semantic results](evidence/ax-semantic-results.json) and [known-layout results](evidence/reduced-blind-results.json) establish surviving action routes. The field and button use only the disposable local fixture.

## Captures remain separate from actions

The matched control marker appeared in all three repetitions of window capture, system window screenshots, and compositor crops. The reduced-exposure marker appeared in none of the tested window or compositor captures. System window screenshots failed. These are route-specific capture observations on this OS.

The compositor adapter crops inside the opaque research window. It checks foreground ownership before and after capture, then discards the image if focus changes. It does not save other applications' windows or desktop content.

The vision agent could not locate a field in the reduced captures, so those action trials are inconclusive. The result does not establish input prevention. The completed AX and known-layout actions already reject agent-free operation. See the [compositor comparison](evidence/compositor-results.json).

## Repeat the attacks

The runners require the loopback fixture and effective probe grants. Rebuilt ad hoc probes can need the same approved registrations refreshed. Each global input event now checks that the research target still owns foreground focus.

```sh
bash scripts/build.sh
bash scripts/build-probe.sh
python3 tools/run_native.py --targets InspectableControl SecureInputExperiment --routes hid keycodes-hid --repetitions 3 --output artifacts/secure-events
python3 tools/run_native.py --targets InspectableControl ReducedExposureExperiment --routes ax blind-fixture --repetitions 3 --output artifacts/reduced-actions
python3 tools/run_capture.py --targets InspectableControl ReducedExposureExperiment --repetitions 3 --output artifacts/reduced-captures
```

No input rule, physical baseline, or mouse classifier follows from these results. The next input hypothesis uses independent device observations and needs its own controls.
