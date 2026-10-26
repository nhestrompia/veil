# Bounded private-entry protection

Milestone 92 adds an experimental protection owner for explicit private-entry sessions. Two fresh stable-engine diagnostics pass their runtime controls. Aggregate Secure Event Input remains on before all fifty-two transition keys and thirteen resumed keys in each run. The delayed per-view flag remains visible in the evidence. The independent session owner covers that measured interval.

The owner checks actual application activation, key-window state, visibility, miniaturization, and foreground process identity. It balances its own enable/disable calls. It refuses admitted diagnostic input when the session expires, native focus is lost, or protection is unavailable. It releases on focus loss, hide, close, application termination, explicit completion, or timer expiry. It installs no global input hook and reads no page content or typed text.

The session lasts up to ten seconds while the process can run. Its timer is cooperative. A stopped UI process cannot execute release code until it resumes. The policy rejects input after an expired deadline when execution returns. This design does not solve the confirmed process-signal route.

| Control | Initial run | Final run |
| --- | --- | --- |
| All transition-key aggregate flags true | Pass | Pass |
| Native focus-loss release | Pass | Pass |
| Readable reference task after release | 1 accepted | 1 accepted |
| Fresh private session after return | 1 accepted | 1 accepted |
| Aggregate protection off after completion and cleanup | Pass | Pass |
| Timer expiry and independent off-state observation | Not tested | Pass |

The final run adds a dedicated idle session before the transition sequence. Its timer releases protection after ten seconds. The external controller observes Secure Event Input off before the next session begins. Across both runs, nine acquisitions match nine successful releases. Each candidate completes six private tasks, and each readable reference completes one external AX task. All temporary processes pass cleanup.

Apple warns that retained Secure Event Input can affect other applications. Its technical note requires release when secure entry is no longer needed or focus changes. The guard therefore applies only to explicit research sessions and requires the readable-app and release controls. The installed API header also documents balanced enable/disable counts. [Apple TN2150](https://developer.apple.com/library/archive/technotes/tn2150/_index.html).

This is an experimental diagnostic feature. It is not enabled in the frozen physical browser, and it has no production user interface. Its admission rule uses native state rather than page-specific fields or event-source metadata. Physical-human usability, permissioned keyboard-observer resistance, arbitrary websites, and broader external attacks remain separate requirements. The native view still updates its own editor flag asynchronously.

All 56 pure private-entry checks and 124 Python checks pass. The ordinary diagnostic is restored without delayed transitions, private-entry sessions, or resumed typing. This prevents future attack runs from overlapping private generated input. The frozen browser and permissioned probes remain unchanged. [Evidence](evidence/private-entry-results.json) includes per-key snapshots, expiry, reference task outcomes, balanced releases, engine identities, and cleanup.

Run `python3 tools/run_password_transitions.py --output artifacts/new-private-entry --private-entry-session` with a fresh output path to repeat the experiment. The process-signal bypass remains open. Live Endpoint Security denial still requires the Apple-granted entitlement that this project lacks.
