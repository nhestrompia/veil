# Direct renderer Accessibility root calibration

The new renderer helper finds only WebContent processes attributed to the exact research browser. The user approved its separate Accessibility grant. A fresh signed-app preflight confirms effective access.

The direct-renderer action reference did not work. Its first application root supplied no role or descendants. After an ordinary host AX query initialized WebKit accessibility, a second reference exposed an `AXApplication` role but still no descendants. Neither reference recovered the page marker, found the fixture controls, or completed an action.

The controller stopped at each failed reference. It skipped candidate AX queries. These are adapter failures, not prevention results. Both references and both helper launches passed exact process cleanup.

## Ownership and action boundaries

The helper accepts only the built InspectableControl and DeviceKeyboardExperiment executables. It checks process start times before later queries. A renderer must use an exact system WebContent path and report the research host as its responsible PID. The observed renderer executable uses the macOS Cryptex path. Both exact system paths are allowed. Similar paths and unrelated owners are refused.

Responsibility lookup uses a private OS metadata API. It belongs only to research tooling, not the proposed browser MVP. Objective-See's [original implementation](https://github.com/objective-see/FileMonitor/blob/master/Library/Source/FileMonitor.m) declares and resolves the same PID lookup. This metadata establishes the selected research cohort for these tests. It does not attest page contents or people.

The helper refuses elements owned by another PID before attribute reads. It saves role counts, fixture availability, and matching disposable AFB markers. It saves no arbitrary text or key codes. Action attempts require the exact loopback fixture URL, known field and button labels, and foreground ownership. No input hook, keyboard synthesis, or mouse synthesis runs.

The approved helper executable is `59600752f1b5672b0080cda4c5975c8bbfdbf80d47ed5f9e0819d88d8d871aa8`. Browser and NativeProbe remain unchanged. The physically calibrated browser remains PID 61893, with its single accepted baseline action.

## Next adapter hypothesis

Current WebKit test code obtains a remote accessibility child token before it creates a client element. It also initializes accessibility through the host view. This explains why a renderer application root alone is not an adequate positive control. It does not prove that a restricted host exposes a token. See [WebKit's client test change](https://commits.webkit.org/306715@main).

AltTab's [original AX wrapper](https://github.com/lwouis/alt-tab-macos/blob/master/src/macos/api-wrappers/AXUIElement.swift) constructs process-scoped remote tokens for bounded element-ID discovery. This supplies a separate research hypothesis. No token enumeration ran in this milestone. Any such test must preserve exact research ownership and pass a real reference before candidate conclusions.

## Verification

All 70 Python checks pass. Swift boundary checks cover both real system paths, unrelated owners, forged paths, invalid PIDs, and unsafe fixture URLs. The signed helper compiles with warnings as errors and passes signature verification.

The [saved results](evidence/renderer-root-results.json) include the failed root controls and the host-initialized retry. The missing grant path queried no AX element. Safari's developer setting remains restored to off. No new candidate action or agent-free claim follows.
