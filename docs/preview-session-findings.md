# Combined preview with a physical control

Milestone 134 tests the unchanged AgentFreeBrowserPreview after the user enables its approved Input Monitoring grant. The user completes the local form with the built-in keyboard. The independent fixture records one accepted action, and the browser logs device binding. The same process remains open for the attacks.

The executable SHA-256 is `dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70`. The live session begins as PID 2892. Its physical result is separate from earlier device and protected-video experiments.

## Scoped external results

| Route | Readable reference | Combined preview |
| --- | --- | --- |
| Independent-window screenshot | Exact page marker before and after | Successful capture, black image, no marker |
| Display screenshot including the target window | Exact page marker before and after | Successful capture, black image, no marker |
| Direct accessibility reads | Page marker and fixture controls available | Application/window metadata, no page marker |
| AX set-value and press | One accepted fixture action, API results zero | Fixture controls not found, no new submission |
| Playwright scripting | Isolated headless Chrome attaches and completes one action | No TCP listener on the preview host, no CDP attachment attempted |

Local image inspection agrees with the screenshot scorer. Each preview image is 2000 by 1544 pixels. These are completed captures, not missing frames. The physical completion and captures use the same browser process and executable. One physical task and two screenshot routes do not establish general browser usability or universal capture protection.

The first read sequence stops before candidate capture because its foreground calibration fails while the reference is open. The reference then stops. The follow-up verifies candidate foreground state and captures both routes. A fresh clear reference supplies the after checks. No failure counts as a blocking result.

The ordinary AX tree and direct queries expose only host metadata in the preview. The AX action helper cannot find its exact fixture field and button. Its raw verdict remains inconclusive. This is not a tested API rejection or proof against every accessibility path. Independent renderer reads remain open.

The Playwright control uses a new headless Chrome profile and a fresh local trial. The fixture independently accepts its action, and its debug port closes after cleanup. The preview host has no TCP listener. That observation does not test Web Inspector over other transports and does not establish inspection prevention.

## Native input safety gate

NativeProbe reports effective Accessibility, event-posting, and Screen Recording access. It also reports modifying mouse hooks owned by LinearMouse, PID 63961, and DockDoor, PID 64027. Exact process metadata identifies those applications.

No CGEvent or HID input is posted. The existing safety guard refuses this environment because of the earlier click failure. The AX action test sets attributes and presses exact disposable fixture controls through Accessibility APIs. It sends no mouse or keyboard events.

The next native-input step needs the two modifier apps inactive. The [resume plan](evidence/preview-input-resume-plan.json) proposes temporary normal quits, fresh hook checks, bounded matched tests, and restoration after all input probes stop. Milestone 135 later completes the approved plan. See [native findings](preview-native-input-findings.md). No unrelated application or setting changes in this milestone.

## Session and code

The new controller owns one preview process and a private loopback fixture. Its controller file stays inside project artifacts with private file permissions. It checks the approved image hash, strict signature, and effective grant before opening the browser. It rejects duplicates, supports a stop file, and has a one-hour cleanup alarm. No test keys or alternate browser entry point enter the preview executable.

The session adapters now accept the pinned preview as well as the earlier keyboard browser. They use each session's fixture controller. The oracle normalizes string and Path inputs at its file boundary. Seventeen session, safety-gate, and reference tests pass. Python compilation passes. The preview and all earlier granted helper images retain their hashes.

All transient native probes and readable references stop. The preview and its fixture remain intentionally live for the next attacks. The controller does not certify physical origin. The separate physical-control record stores the user's declaration and independent receipt. No new candidate submission follows the read or AX trials.

See [saved results](evidence/preview-session-results.json), [preview capture](evidence/preview-session-black.png), and [readable control](evidence/preview-session-control.png). Agent-free browsing remains unproven.
