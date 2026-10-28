# Native input against the combined preview

Milestone 135 tests the same AgentFreeBrowserPreview process that passed the user's physical form task. PID 2892 and its executable hash remain unchanged. The independent fixture retains exactly one accepted submission after the comparison. That submission is the earlier physical control.

## Results

Each route first targets a fresh readable reference. Only a successful reference permits input against the preview. The native probe checks for modifying mouse hooks before input. The candidate uses the reference field position, translated through public window geometry.

| Input route | Reference actions | Preview result | Refused events |
| --- | --- | --- | --- |
| HID-source CGEvent | 1 | Blocked | 29 |
| HID-source hardware key codes | 1 | Blocked | 29 |
| Curved mouse path and HID-source typing | 1 | Blocked | 90 |
| Session-source CGEvent | 1 | Blocked | 29 |
| Private-source CGEvent | 1 | Blocked | 29 |
| Direct-to-process HID-source events | 0 | Skipped, inconclusive | Not attempted |

The five calibrated attacks produce 206 explicit refusals, zero admitted events, and zero new preview submissions. Every tested reference and candidate has verified foreground activation. The direct-to-process reference receives pointer movement and keydown events but completes no action. The comparison stops there. No candidate result follows from that failed control.

The process-directed keyboard variants and two IOHID routes do not run. Combined screenshot/OCR/input trials also remain open on this preview. Earlier results from other browser images do not fill these gaps.

## Approved app pause and cleanup

The user approves temporary normal quits of LinearMouse and DockDoor, followed by restoration. The helper checks both bundle identity and the exact application and executable paths. Both applications accept normal termination. The probe then reports an available mouse-hook list with no modifying hooks.

The controller stops after the failed reference and checks that no NativeProbe process remains before restoration. Both modifier apps reopen successfully. A later permission check detects their modifying hooks again. The native input guard therefore prevents further posting in the restored environment.

All six readable references stop. The preview and its private fixture remain live under their existing one-hour watchdog. No root access, computer-use service, preference change, force quit of a modifier app, or additional app pause occurs.

## Code and evidence

`ApprovedModifierPause.swift` contains only the two approved application identities. `run_preview_native_comparison.py` checks the pinned physical session, runs routes serially, stops on an inconclusive result, and restores the original apps. Its cleanup path refuses restoration while a native probe remains active. After the live comparison, the runner also gains a consumed-approval guard and records restoration errors. These changes do not trigger another live run.

The helper compiles with Swift 6 and warnings as errors. All 21 Python checks pass. These include restoration after attack failure, stopping after an inconclusive result, refusing restoration during an active probe, and refusing a consumed approval. Python compilation passes. All 11 permissioned executable hashes and the preview's browser source hashes remain unchanged.

See [saved results](evidence/preview-native-input-results.json) and [the approved plan](evidence/preview-input-resume-plan.json). Full route records are in `artifacts/integrated-browser-135/native-comparison/`.

The current preview now has a successful physical control, two black scoped screenshot results, and five calibrated native-input refusals. Agent-free browsing remains unproven. Independent renderer accessibility, other inspector transports, continuous capture of this exact preview, and autonomous page actions remain open. Mouse support and general website compatibility also remain incomplete.
