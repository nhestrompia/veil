# Current research state

Updated 2026-10-25. Milestones 50 and 51 are committed. Milestone 52 completes a Safari remote-inspector control and records candidate discovery. Agent-free operation remains unproven.

## Current priority and remote control

The user clarified that recognizing physical typing is separate from agent-generated input. Do not count that observation as an autonomous input bypass. Prioritize navigation and website actions by external agents. Keep confidentiality results separate.

Safari Web Inspector read the reference marker and completed one accepted task. The working reference appeared in the Mac target menu, while the unchanged candidate did not. This is a not-advertised result, not a direct attachment refusal. See [remote findings](safari-remote-findings.md).

The user approved a temporary developer-setting toggle and restoration. The UI confirmed its final state was off. Research Safari windows closed and the reference passed cleanup. A broader inspection-list read was rejected because of unrelated tab URLs. The safer Mac-only menu completed discovery.

DockDoor and LinearMouse had restarted. Their verified processes stopped before input, and the safeguard then reported no blocking hooks. Recheck before every later attack.

## Latest result

The external observer matched the fixed fake phrase through both Unicode and virtual-keycode matchers. It received sixteen events while the restricted browser accepted one requested physical task. The controller generated no input. Device binding and unchanged identity were confirmed. The listener stopped on focus loss, removed its tap, and passed cleanup.

The current generated reference matched both decoders and completed one task. It is not a physical reference. This would limit negative conclusions, but the candidate observation was positive. See [the readiness findings](keyboard-readiness-findings.md) and their saved evidence.

Earlier physical attempts remain inconclusive. Their observer deadlines started too early. Earlier PIDs 43980 and 58504 stopped without a matching crash report. Their exit causes remain unknown. Do not attribute their completed attack matrices to the new PID.

## Live session and frozen identities

The capture-restricted browser is PID 61893. Its session file is `artifacts/source-policy-live/keyboard-observation-ready-session.json`. The fixture and caffeinate remain in unified exec session 53557. No observer or controller remains active. The empty replacement readable control was closed with exact executable verification.

- Browser SHA256: `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`.
- NativeProbe SHA256: `7c256598528dcaf2dcdc6437af30dab92d9c4ca929a55a3a2402f09754f67de1`.
- KeyboardObservationProbe SHA256: `cdd1829e60dd838f5a2b1ef91f9d5635e7f61760360f9c18c494f8eb90086aac`.

Keep these executables frozen during matched tests. The observer has effective Accessibility and listening access. The user approved its exact Accessibility Add and its app-only reset followed by re-add. No other permission reset follows from that approval. No permission question is pending.

To stop the exact browser:

```sh
python3 tools/run_device_session.py stop --session artifacts/source-policy-live/keyboard-observation-ready-session.json
```

Stop the fixture separately when live work ends.

## Completed boundaries and remaining work

The original physical process refused 27 calibrated native attempts and three adaptive vision attempts. Window and filtered-display images were black. System screenshots and unavailable AX actions remain inconclusive. Fifteen startup comparisons and eighteen session-insertion refusals are separate diagnostic results.

The current observation disproves keyboard confidentiality against this permissioned listener. The generated password comparison received no keys during two accepted tasks. Secure input was active, and cleanup restored its inactive state. Physical password entry remains untested. See [the secure-entry result](secure-entry-observation-findings.md). Apple TN2150 advises against enabling Secure Event Input for general text or an entire app lifetime. Do not turn that into a whole-browser fix without a separate design and compatibility experiment.

Direct remote attachment beyond discovery, unfiltered capture on this physical build, renderer semantics, broader session privacy, and general website compatibility remain open. The browser supports only the measured built-in keyboard and US ASCII. Pointer input is disabled. The device policy does not attest a human or cryptographically attest hardware.

All 66 Python checks pass. Swift matcher and timing checks pass. See [implementation milestones](implementation.md) for the full record.

## Desktop safeguards

Check effective permissions and `desktopInputSafety` before input. Refuse unavailable checks or modifying mouse hooks. Never install modifying global taps, seize devices, reset global TCC state, kill tccd, or bypass guards.

The earlier click failure cleared after DockDoor stopped. Its exact cause remains unknown. Do not reproduce it. The browser reader is non-seizing and routes keys only while its window is key and frontmost.

The observer uses a PID-scoped listen-only key-down tap. It decodes only while the exact research target owns focus. It saves no raw text or key codes. The first key starts a fifteen-second sample after at most sixty seconds of idle wait.

Do not select the AX-hidden browser through computer use. That path stalls. Refresh computer-use documentation before UI work. Selecting a closed readable control can create an empty replacement window. Verify exact process identity.

No branch was pushed and no pull request was created. The historical pause note below concerns earlier builds.

---

# Research paused

Paused at the user's request on 2026-10-24. Do not resume tests without a new instruction. The local fixture and its keep-awake process stopped. No project research application remained during the final cleanup check.

## Current result

The browser is not proven agent-free. The native probe's existing grants and the browser's existing Input Monitoring grant were refreshed through System Settings. No new permission scope was added.

Milestone 29, commit `9382485`, restored native calibration. Nine of eleven reference routes completed their task. Two PID-directed mouse routes remain inconclusive. The native runner now skips candidates without successful matched references.

Milestone 30, commit `c1c40e7`, added paired legacy HID releases and hardened startup-test cleanup. All 25 Python checks pass. Fifteen references completed their task, and fifteen matched fresh-start candidates admitted no input or website action. Every candidate had a ready device reader, with no binding observed. Every process passed cleanup. This does not establish usability after physical binding or hardware attestation.

## Capture milestone completed before pause

The controller now also tests the system screenshot tool against the exact research window. The capture runs finished before the pause request.

| Route | Readable references | Restricted diagnostics |
| --- | --- | --- |
| ScreenCaptureKit stream with an owned backdrop | Marker recovered in 3 of 3 | Marker absent in 3 of 3. Research backdrop recovered in all three. |
| ScreenCaptureKit window image | Marker recovered in 3 of 3 | Marker absent in 3 of 3 captured images. |
| System window screenshot | Marker recovered in 3 of 3 | All three capture commands failed. These are inconclusive results. |

All twelve diagnostic processes completed one internal form action. These are private bootstrap controls, not physical-human controls. The latest restricted binary still needs physical visibility and usability evidence before any agent-free claim.

Raw results are under `artifacts/capture-after-recovery/`. The four directories are `visible`, `restricted`, `window-visible`, and `window-restricted`, each with trials `0` through `2`. The first two contain stream runs. The other two contain window and system screenshots.

## Desktop safety

The earlier physical click failure cleared after DockDoor stopped. Stopping the computer-use service and LinearMouse alone did not clear it. The exact interaction remains unexplained. Do not reproduce that failure on the user's desktop.

LinearMouse restarted during later work. The new guard refused input before launching a browser. A normal quit followed by an immediate bounded trial isolated the input path. Recheck active hooks before future input. Do not silently bypass the guard.

The diagnostics have termination timers, and controllers verify exact executable cleanup. Native CGEvent and legacy HID adapters release their own pending input after errors. Forced process termination still cannot establish an absolute input-release guarantee.

## Resume points

1. Read this note and use `but diff` for pending changes. Raw Git index status is stale under this GitButler workspace.
2. Confirm the current probe hash, effective grants, console access, and mouse-hook status. Rebuilding the probe can invalidate its grants.
3. Calibrate references with the exact current probe before candidate attacks. Earlier reference hashes cannot replace new calibration.
4. Continue same-process attacks after a valid physical binding. Physical usability on the latest restricted build remains unverified.
5. Keep Safari inspector attachment and adaptive mouse-behavior research separate. Neither has a completed result in this pause milestone.

The final diagnostic build in `dist/InternalKeyboardControl.app` is capture-restricted, without the full-screen backdrop. It has a private startup sequence and no physical device reader. `DeviceKeyboardExperiment.app` remains the separate keyboard-only research browser.

No branch was pushed and no pull request was created during this session.
