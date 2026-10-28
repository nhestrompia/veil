# Cross-app drag delivery

Later [session recovery](session-recovery-findings.md) adds working external drag-entry controls. Full text-drop delivery remains inconclusive.

The new research adapter tests text delivery through an AppKit dragging session. This route needs a separate experiment because the keyboard browser filters ordinary input events. A drag destination can receive a different callback path.

The source app owns a new pasteboard item containing only `native-input`. It never reads or writes the general clipboard. The native probe starts a drag from that source to the disposable page field. Before each posted point, it checks foreground ownership and the covering window. Both endpoints and the complete path must stay inside the research browser frame. A non-research covering window stops the attempt.

The fixture has an optional `submit-on-input=1` mode. That mode submits the normal form when its field receives the exact fixed text. The independent server still records only the accepted outcome. The default fixture behavior stays unchanged.

## Public refusal policy

The keyboard experiment now returns an empty operation during drag entry and update. It refuses preparation and import. These callbacks cover the owned web view, window, address field, and a dedicated field editor. Refusal logs contain only the callback phase. Other browser variants retain their earlier behavior.

The [internal browser diagnostic](evidence/drag-keyboard-controls.json) confirms that the address uses the dedicated editor. Normal Return submission completes one fixture action. A separate input-triggered control also completes one action, without the final Return key. These are browser-function controls. They do not establish external drag prevention.

## Milestone 24 result

The adapter and source app compile with Swift 6 warnings as errors. The controller compiles, and the existing internal event-gate check passes. There is no successful external drag control yet.

The [saved preflight](evidence/drag-preflight.json) records ineffective grants for the rebuilt probe. It launched no drag target and sent no drag input. Advisory console metadata reports a locked session. System Settings observations also returned `cgWindowNotFound`. These failures are inconclusive. They supply no evidence of drag prevention.

The controller requires the approved posting and capture grants before it starts a trial. Every comparison creates a fresh reference and diagnostic browser process. The diagnostic bootstrap supplies a loaded page without a new physical test. It does not establish human usability or physical device origin. The runner counts only new accepted form actions after that bootstrap.

The separate [source investigation](research/drag-delivery-boundary.md) examines macOS drag callbacks and possible public API defenses. Source reasoning does not replace a working external control.

```sh
bash scripts/build-drag-source.sh
bash scripts/build-probe.sh
bash scripts/diagnose-browser-keyboard.sh --build-only
python3 tools/run_drag_delivery.py --repetitions 3
```

Rebuilding an ad hoc probe can invalidate its effective grants. The already approved permissions need an equivalent refresh through normal System Settings before the live comparison. No additional permission scope is part of this experiment. The agent-free goal remains unmet.
