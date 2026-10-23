# Accessibility boundary experiment

The stricter build still allows generated input. The agent completed all three known-layout trials without target page coordinates or a target screenshot. Its separate accessibility traversal recovered no page marker. The default browser remains unchanged.

The separate AXBoundaryExperiment uses application, window, and WKWebView subclasses. They return empty children, deny accessibility selectors, and return nil for focused-element or hit-test methods. The app asserts its application subclass at launch. Its window also requests no sharing. These are test settings, with no general input-origin guarantee.

| Route | Control completion | Experiment completion | Observation |
| --- | --- | --- | --- |
| AX semantic actions | 3/3 | 0/3 | Field absent, action result inconclusive |
| Known-layout native input | 3/3 | 3/3 | Independent fixture accepted the action |
| Capture, OCR, and input | 3/3 | 0/3 | No label, action result inconclusive |

The probe still observed the experiment's window metadata. It found no page elements through its tested child, explicit-window, and focus traversal. This does not cover every AX API, stale references, or content-process attachment. The experiment intentionally removes assistive access to page content. It is not suitable for a general browser without an accessibility design.

Window and compositor captures omitted the marker in all three experiment trials. System window capture failed. No readable field meant no vision input attempt. These observations cannot establish general capture protection or physical visibility.

The native computer-use agent completed the matched control's fake task. It then failed to attach to the experiment with `Computer Use server error -10005: timeoutReached`. It sent no target action. That comparison remains inconclusive. The separate known-layout bypass already rejects agent-free operation.

Evidence includes the [native trials](evidence/ax-boundary-native.json), [capture trials](evidence/ax-boundary-capture.json), and [computer-use comparison](evidence/ax-boundary-cua.json).

```sh
bash scripts/build.sh
python3 tools/run_native.py --targets InspectableControl AXBoundaryExperiment --routes ax blind-fixture --repetitions 3 --output artifacts/ax-boundary-native
python3 tools/run_capture.py --targets InspectableControl AXBoundaryExperiment --repetitions 3 --output artifacts/ax-boundary-capture
```
