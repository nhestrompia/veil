# Current research state

Updated 2026-10-25. The browser remains unproven as agent-free. Milestones 35 through 45 are complete and committed on `native-feasibility`. Milestone 46 packages the observer and records the approved effective grant.

## Live physical session

One capture-restricted `DeviceKeyboardExperiment` remains alive as PID 43980. Its session file is `artifacts/source-policy-live/physical-session.json`. The user reported Task complete. The independent oracle recorded one accepted physical task, a ready device reader, and binding to the measured built-in keyboard.

The browser hash is `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`. NativeProbe hash is `7c256598528dcaf2dcdc6437af30dab92d9c4ca929a55a3a2402f09754f67de1`. Neither changed during the physical-session attacks. Do not rebuild either binary before any remaining same-process test.

The fixture and caffeinate remain active as unified exec session 53557. No attack controller or observer remains active. Keep the current browser available for the remaining keyboard observation comparison.

To stop this exact browser, run:

```sh
python3 tools/run_device_session.py stop --session artifacts/source-policy-live/physical-session.json
```

The controller verifies executable identity and waits for exit. Stop the fixture separately when live testing ends.

## Verified results

- Milestone 41: twenty-seven native attempts received explicit refusals, with zero admitted events and no new accepted action. Six failed-control cases were skipped.
- Milestone 42: three adaptive vision controls completed. Three matched known-layout curved attempts received explicit refusals. The target window images were black. The repaired controller preserves earlier adapter failures as inconclusive.
- Milestone 43: three filtered-display references disclosed their markers. Three restricted images were identical and black. System window screenshots worked on three references but failed on the candidate. Those failures remain inconclusive.
- Milestone 44: all three AX references disclosed markers through both read routes and completed a task. Candidate reads recovered no marker and exposed no content menu actions. The action adapter found no field and remains inconclusive.
- Milestone 45: the passive keyboard observer compiles. It has no effective Accessibility or listening grant. Its preflight and no-grant observe path install no monitor. An unrelated PID is refused.

All 52 Python checks pass. The passive observer compiles with warnings as errors. Earlier source-policy and dispatch checks pass. Recent findings and saved evidence are linked from README and `docs/implementation.md`.

The fifteen source-policy startup comparisons, eighteen session-insertion refusals on loaded diagnostics, and offline behavior pilot remain separate results. Annotated-insertion controls did not complete. The offline pilot trains no classifier and supplies no live replay result.

## Observer authorization and next control

The signed app is `dist/KeyboardObservationProbe.app`, bundle `research.agentfreebrowser.keyboardobserver`. The user explicitly approved adding this exact app to Accessibility. The Add selected the exact bundle, and System Settings showed its switch on. A fresh app preflight now confirms effective Accessibility and listening access. No monitor ran during that check. No permission question remains pending.

Only this app's Accessibility addition was authorized. No global reset or other permission change is authorized. The observer supports only preflight and observe with an exact research PID. It has no permission-request command. Keep its executable frozen after a grant.

The code uses a passive AppKit monitor. It requires exact foreground ownership and a target-owned event window before text extraction. It stops on focus loss or after fifteen seconds. It saves counts and a fixed fake-phrase match, with no raw text or key codes. A readable physical-key reference must work before candidate results count. Do not replace physical input with an agent-generated sequence.

A generated readable control completed its task. The AppKit monitor received thirteen copies but discarded them because window ownership was unavailable. Both process cleanups passed. That is an adapter limitation, not prevention. The proposed next adapter is Apple's per-PID listen-only tap. It is not implemented yet.

The physical task occurred before the observer existed. It cannot establish keyboard confidentiality. The source review is `docs/research/keyboard-observation-boundary.md`.

## Remaining acceptance gaps

The current evidence does not establish unfiltered capture protection, external remote-inspector prevention, renderer-wide semantic isolation, or browser-session privacy. The current probe's isolated compositor command accepts only the old two-window internal diagnostic. Do not repurpose that result as a current physical-browser result or bypass its backdrop guard.

The source policy permits one observed hardware path. It does not cryptographically attest a person or hardware. Pointer input, Unicode, broad website compatibility, VoiceOver, and the PRD's human sample remain unmet. A single fake task cannot support a general-usage claim.

## Desktop safeguards

Before input, check effective grants and `desktopInputSafety`. Refuse unavailable checks or modifying mouse hooks. Never install a modifying global tap, seize a device, reset global TCC state, kill tccd, or bypass a guard.

The earlier desktop click failure cleared after DockDoor stopped. Its exact cause remains unexplained. Do not reproduce it. The browser's reader is non-seizing and only routes keys while its own window is key and frontmost.

Do not bind the AX-hidden DeviceKeyboard app through native computer use. That path previously stalled for minutes. Use the scoped probe and verify exact PID and binary identity. Current native UI bindings are `grantSettings` and `grantFinder`. Refresh computer-use documentation and UI state before reuse.

The DeviceKeyboard grant is now effective after the user's approved one-app ListenEvent reset and exact-bundle Add. Earlier off/on and Add attempts failed. No further DeviceKeyboard refresh is needed.

No branch was pushed and no pull request was created. Historical pause notes below describe earlier builds and do not override this current state.

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
