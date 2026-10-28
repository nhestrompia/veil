# Desktop input recovery and test safeguards

Desktop attacks paused after the user reported that the pointer moved but app clicks failed. No research application remained. Stopping the computer-use service did not restore clicks. Stopping LinearMouse did not restore clicks. Clicks returned after DockDoor stopped, as the user confirmed.

A read-only event-tap query found modifying mouse hooks from LinearMouse and DockDoor. The recovery sequence implicates DockDoor, but it does not establish the internal cause or how a research test triggered it. No system input setting or privacy database changed during recovery.

## Test changes

The probe now refuses input commands when modifying mouse hooks are active or their status is unavailable. The drag source checks the same condition before opening its window and before each drag. The drag controllers check it before launching targets. The check reads process IDs and event masks only. It does not record input contents. This is a test safeguard, not a browser security boundary.

A failed drag previously attempted mouse release through the same ownership checks that caused the failure. Release now runs independently after a successful button press. Key and click adapters also release their own pending input on failure. Research ownership checks still apply to new input.

The source now uses a floating window instead of a screen-saver window. Source and internal-control diagnostics have termination timers. Controllers wait for verified application exit and use a final stop signal if needed. A readiness failure also stops newly launched instances of the exact research executable. Existing instances and unrelated executables remain outside cleanup.

## Checks and limits

All 23 Python checks pass. They cover unavailable hook status, active hooks, graceful exit, stalled processes, PID replacement, and failed readiness. A real disposable process received termination and exited. Swift checks cover modifying, observing, disabled, keyboard-only, and mouse-release hooks. Browser policy checks pass all 12 cases, and device-dispatch checks pass.

The rebuilt probe reports both mouse-hook owners and refuses input before any browser launch. Its new signature requires the existing probe grants to become effective again. No new desktop attack ran in this milestone.

This does not prove the physical click failure cannot recur. The exact DockDoor interaction remains unexplained. Earlier failed CGEvent controls remain inconclusive. New input trials require an isolated mouse path and a successful reference task.
