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

A future comparison needs a physical fake sequence in a readable ordinary field, then the unchanged restricted browser. A password-field comparison must retain its separate category. An agent-generated phrase cannot replace a physical-key control.

The [source review](research/keyboard-observation-boundary.md) explains why this route matters. AppKit observation, Quartz listen-only taps, Accessibility, and Input Monitoring are distinct cases. None receives a pass from this preflight.
