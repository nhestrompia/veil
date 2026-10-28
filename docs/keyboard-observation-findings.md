# Passive keyboard observer preflight

A separate observer now compiles with Swift 6 and warnings as errors. It uses the read-only AppKit global monitor API. Its default preflight checks existing permission state without installing a monitor or requesting access.

The standalone executable reports no effective Accessibility or keyboard-listening access. Its observe command refuses to install a monitor. An unrelated PID also fails the target check with exit code 2. The [saved preflight](evidence/keyboard-observation-preflight.json) records those results and the executable hash.

No keystroke observation test ran. No physical reference was collected, so this milestone supplies no disclosure-prevention result. The existing browser and NativeProbe binaries stayed unchanged.

## Scope of the prepared experiment

The probe accepts only a running research browser or its readable reference. It requires that exact PID to own foreground focus. Before reading an event's characters, it also requires the event's window number to belong to that PID. Missing ownership data causes it to discard the event. The readable reference must validate that strict rule before any candidate comparison.

The passive callback cannot change or stop event delivery. The process stops after focus loss or fifteen seconds. It removes its monitor on normal completion. It saves only event counts, the fixed fake phrase's match status, authorization state, and cleanup state. It saves no raw text or key codes.

The fake phrase is native-input. It is fixed in source. There is no arbitrary text argument, grant request, global modifying tap, or device seizure.

## Commands

```sh
bash scripts/build-keyboard-observer.sh
.build/keyboard-observation-probe preflight RESEARCH_PID
.build/keyboard-observation-probe observe RESEARCH_PID
```

The observe command requires an effective existing Accessibility grant. This new executable does not inherit NativeProbe's grant. No permission request follows automatically.

The build also creates `dist/KeyboardObservationProbe.app` with a separate bundle identity. Its signature verifies, and an app launch confirms the same absent grants and zero collected events. The app supports the same preflight and observe arguments. The user then approved adding this exact app to Accessibility. System Settings showed its switch on. A fresh app launch confirmed effective Accessibility and listening access, with zero events and no monitor installed. The packaged executable remains frozen. The source contains no permission-request command.

A future comparison needs a physical fake sequence in a readable ordinary field, then the unchanged restricted browser. A password-field comparison must retain its separate category. An agent-generated phrase cannot replace a physical-key control.

The [source review](research/keyboard-observation-boundary.md) explains why this route matters. AppKit observation, Quartz listen-only taps, Accessibility, and Input Monitoring are distinct cases. None receives a pass from this preflight.

## Generated control after the approved grant

The readable task completed through generated input. The observer received thirteen key copies but discarded all of them before text extraction. Their window numbers did not identify a target-owned window. It matched no fake phrase. Both processes passed cleanup.

An earlier controller attempt stopped before observer launch because it expected the label in AXDescription. The actual label was in AXTitle. The evidence records a transcript summary of that failure. Its output directory was reused.

This generated control is not a physical reference. It also exposes a limit in the observer's ownership filter. Neither miss supports a prevention claim. A PID-scoped listen-only tap is the next proposed adapter. Apple documents that separate API. No active or modifying global tap is needed. [Apple PID tap API](https://developer.apple.com/documentation/coregraphics/cgevent/tapcreateforpid(pid:place:options:eventsofinterest:callback:userinfo:))
