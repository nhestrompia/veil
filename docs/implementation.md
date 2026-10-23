# Implementation milestones

## Milestone 1: native research shell

Implemented October 23, 2026, on macOS 26.6, build 25G72, arm64, with Apple Swift 6.4 and the macOS 27 SDK.

The browser contains one WKWebView with inspection disabled and a nonpersistent website data store. It exposes no external page-read, snapshot, or evaluation API. A separate control binary enables inspection at compile time. Both app bundles use Hardened Runtime, an ad hoc signature, App Sandbox, and network-client access. This is a research build, not production distribution.

The loopback fixture owns submission outcomes outside the browser. Controller requests need a random key in a local, ignored file. This prevents accidental validation through browser state. It does not isolate the fixture from unrestricted same-user code. Direct HTTP submissions are oracle tests, not browser-attack evidence.

Two architecture sketches and an independent judge compared direct Swift compilation with SwiftPM. The judge preferred the Python fixture and separate executables. The implementation keeps those boundaries and uses direct compilation for the smallest first build. A Swift HTTP server and a shared browser/attacker library were rejected as unnecessary initial work.

Verification completed:

- Both signed app bundles compile with Swift 6 and warnings treated as errors. Signature verification passes.
- Twelve policy cases cover HTTPS, loopback HTTP, and rejected schemes or hosts.
- The fixture test covers controller authorization, independent trial outcomes, and removal of typed data from event telemetry.
- The protected app loaded the loopback page. Native computer use inspected its window and followed its HTTPS link to example.org.

The native tool exposed the fixture's accessibility content despite disabled inspection. This is an early observation, not a prevention result. Milestone 2 measures reads and actions with an independent oracle.

No human-input baseline, Safari inspector attachment comparison, or capture exclusion result is established by this milestone.

## Run the prototype

```sh
bash scripts/build.sh
bash scripts/test-policy.sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/fixture.py
open -n dist/AgentFreeBrowser.app --args --url https://example.org
```

Use `dist/InspectableControl.app` only as the separate inspection-positive control. The browser accepts HTTPS and loopback HTTP. Clipboard operations remain available for baseline attacks. Full export restrictions are not implemented. The default build has no input defense. The separate filter variant is an experiment with demonstrated bypasses.


## Milestone 2: native attacks

Committed as `548af04`. Added the independent NativeProbe app, permission preflight, CGEvent and AX adapters, paired runner, and strict prevention verifier. See [native-input findings](native-input-findings.md).

## Milestone 3: capture and browser transports

Committed as `6a6eb2b`. Added ScreenCaptureKit and system capture, OCR-driven input, pinned Playwright probes, and separate inspector-discovery evidence. See [capture findings](capture-findings.md).

## Milestone 4: source-state filter

Added `dist/MetadataExperiment.app` and tested the rule against adapted native and vision agents. The generated HID-state events bypassed the filter. See [filter findings](input-filter-findings.md).

The default browser remains an unprotected research baseline. There is no validated behavioral detector or agent-resistant MVP. NativeProbe's user-approved Accessibility and Screen Recording grants remain enabled for repeat experiments. Rebuilt ad hoc binaries need effective-grant checks and may need a fresh registration. Do not grant these permissions to the browser app itself.

## Milestone 5: guarded foreground experiments

Added SecureInputExperiment and ReducedExposureExperiment, with console preflight checks and a cycle-safe AX traversal. Live attacks remain pending because the current graphical session reports a lock. The preflight refuses these trials. See [foreground findings](foreground-findings.md).

## Milestone 6: protected HTML pixels

Added PixelControl and PixelProtectedExperiment with a source WKWebView outside the onscreen window list. The control submitted an HTML snapshot through a sample-buffer renderer. Capture exclusion and human visibility remain unverified. No input bridge exists. See [pixel findings](pixel-rendering-findings.md).

## Milestone 7: independent device observations

Added a separate HIDObservation app and an unentitled virtual-device probe. Both virtual-device APIs returned nil in three creation attempts. Input Monitoring was requested after user approval, but its effective grant remains off. No physical sample, synthetic observation matrix, classifier, or input defense exists yet. See [device findings](hid-observation-findings.md).

## Milestone 8: calibrated routes and pixel formats

Refreshed the approved native grants and replaced the blanket console veto with advisory metadata and matched controls. Added filtered display capture, readiness diagnostics, and NV12 conversion. Matched capture pilots recovered clear control content. The user reported black physical BGRA output while its unprotected control was visible. This rejects that configuration as useful protection. The protected NV12 view also appeared black on the direct display. See [route calibration](route-calibration.md).
