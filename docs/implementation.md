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

Added SecureInputExperiment and ReducedExposureExperiment, with console preflight checks and a cycle-safe AX traversal. Milestone 9 replaces the console veto and completes live attacks. Both policies allow agent actions. See [foreground findings](foreground-findings.md).

## Milestone 6: protected HTML pixels

Added PixelControl and PixelProtectedExperiment with a source WKWebView outside the onscreen window list. The control submitted an HTML snapshot through a sample-buffer renderer. Milestone 8 tests capture routes and physical visibility. Both protected pixel formats fail physical visibility. No input bridge exists. See [pixel findings](pixel-rendering-findings.md).

## Milestone 7: independent device observations

Added a separate HIDObservation app and an unentitled virtual-device probe. Both virtual-device APIs returned nil in three creation attempts. The approved Input Monitoring grant is now effective. Generated-input observations exist. A physical baseline, classifier, and input defense remain absent. See [device findings](hid-observation-findings.md).

## Milestone 8: calibrated routes and pixel formats

Refreshed the approved native grants and replaced the blanket console veto with advisory metadata and matched controls. Added filtered display capture, readiness diagnostics, and NV12 conversion. Matched capture pilots recovered clear control content. The user reported black physical BGRA output while its unprotected control was visible. This rejects that configuration as useful protection. The protected NV12 view also appeared black on the direct display. See [route calibration](route-calibration.md).


## Milestone 9: foreground and semantic bypasses

Added explicit AX window and focus traversal, foreground checks for each generated event, and compositor crops inside research windows. The probe now focuses the fake field before AX value and button actions.

Secure Event Input allowed six native trials, with its mode enabled during all 84 logged input events. The reduced-exposure build allowed all three semantic AX trials and two of three known-layout trials. Its tested captures omitted the marker. These capture observations do not establish input prevention. See [foreground findings](foreground-findings.md) and the saved independent fixture outcomes.


## Milestone 10: isolated graphics-buffer lookup

Added a two-process calibration for direct IOSurface and Core Video allocations. Default and explicit-false allocations returned nil for exact-ID lookup in twelve trials. Six explicit-global controls recovered the exact fake bytes. No browser identifiers, desktop enumeration, or protected-media claim follow from this test. See [surface findings](surface-findings.md).

## Milestone 11: generated-input observations

The observer accepted all fifteen generated-input tasks. Seven trials produced no raw device records. None produced raw keyboard records. Pointer records in other trials remain potentially mixed with physical input. See [generated controls](hid-generated-findings.md).

## Milestone 12: explicit accessibility boundary

Added application, window, and web-view overrides in a separate AXBoundaryExperiment. The tested AX traversal exposed no page marker. The known-layout native agent still completed all three tasks. A computer-use attachment timed out, so that route remains inconclusive. See [accessibility findings](ax-boundary-findings.md).

## Milestone 13: declared physical input

The user supplied a physical session with 97 raw keyboard records. No raw pointer values or accepted fake action appeared. This is a positive keyboard observation, with no complete human-usability result. See [physical-input findings](hid-physical-findings.md).


## Milestone 14: lower-level posting attacks

Added both default and HID-manager options of IOHIDPostEvent to the native probe. All six fake form actions completed. No raw callback appeared in this observer configuration. Apple source still contains a report-producing path. See [posting findings](hid-posting-findings.md).

## Milestone 15: keyboard-only device routing

Added a separate unsandboxed research browser with an approved Input Monitoring grant. The event gate uses exact internal objects through application dispatch. Queue insertion copied the event in the first test, so that design failed.

The user completed one independent website action with the physical keyboard. In the same process, twenty generated-input trials recorded refusal with matched working controls. Four further trials remain inconclusive. No attack added a submission. The build still has an automatic launch-URL route and no pointer support. See [device-keyboard findings](device-keyboard-findings.md).


## Milestone 16: directed keyboard calibration

Added mixed global-click and PID-keyboard routes, with Unicode and physical-key-code variants. Both completed all three controls. The original all-directed route and a window-annotated variant still failed three controls each. The expanded matrix contains 27 completions and six inconclusive results. See [directed-input findings](directed-input-findings.md).


## Milestone 17: physical startup submission

Launch arguments now fill the keyboard browser address without loading it. Three earlier launch trials reached the disposable endpoint. Three revised trials made no requests, with matched controls and effective device access. The latest visible control repeated this zero-of-three result. These are bounded launch results.

Physical startup checks exposed a hidden app and a repeated-Space editing bug. The user confirmed address visibility after explicit app selection. The native field control reproduced address replacement before the dispatcher fix and passed afterward. Repeated binding Spaces now preserve the address until navigation begins. A ready message confirms binding, and normal Space input resumes after navigation.

The shared app path has two mutually exclusive build flavors. The visible flavor enables window sharing for diagnosis. It cannot establish capture prevention. The updated build still requires physical website completion and attacks against that same process. See [startup navigation](launch-navigation-findings.md) and [visibility diagnosis](startup-visibility-diagnosis.md).
