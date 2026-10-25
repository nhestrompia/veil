# Focus filters and the remaining visibility bypass

Two diagnostic changes stopped the original activation-only page action. Both failed a separate visibility-change action. Neither change is enabled in the production source or frozen physical browser.

## Matched results

| Diagnostic | External route | Result | Private typing after return |
| --- | --- | --- | --- |
| AppKit activation-event filter | Activate another window, then return | No new action in three of three candidates | One accepted task in each candidate |
| Same filter | Hide, restore, and activate | Two new actions in each of three candidates | One accepted task in each candidate |
| Logical key-window state | Activate another window, then return | No new action in one candidate | One accepted task |
| Same logical state | Hide, restore, and activate | Two new actions in one candidate | One accepted task |

All matched readable controls completed their expected lifecycle actions. Candidate lifecycle cycles admitted zero input events. The external helper used only NSRunningApplication operations on exact research bundles. It posted no keyboard or pointer input and made no AX call during those cycles. Readable references used AX only to arm their initial form.

The visibility page arms its ordinary document visibilitychange listener after the first accepted task. Hiding and restoring the app each start another accepted task. The independent fixture records both actions. The helper checks actual hidden state and foreground ownership. These actions do not depend on a failed typing adapter.

## Why neither change is a browser fix

The activation filter refuses applicationActivated and applicationDeactivated before AppKit dispatch. That blocks the tested key-state transition. Hiding the app still changes the window and document visibility. The logical-key diagnostic instead reports a constant true key-window value. WebKit retains a separate visibility path, so that change also leaves the second action route open.

Both diagnostics use the shared application gate and protected WebKit configuration. Their initial and resumed tasks use private authorized key objects. They do not start the HID reader, and they do not establish physical usability or hardware origin. The actual foreground-PID guard remains unchanged.

The logical-key getter also affects WebKit's password-related Secure Event Input checks. That coupling prevents promoting a focus-only result as a safe general browser change. See [the source trace](research/focus-boundary.md).

## Password control and cleanup

The readable password reference accepted its initial task and enabled Secure Event Input. The activation-only helper could not establish a move to the sink window. No focus action followed. The controller skipped the candidate. This comparison is inconclusive and supplies no password mitigation result.

All temporary applications passed cleanup. Secure Event Input was off after every final cleanup, including the password attempt. Earlier hide results retained an incomplete operation receipt. The final three-run series verifies hidden state and reproduces the bypass.

## Implementation and next boundary

The diagnostic build script exposes separate activation-filter and logical-key options. A timed private second sequence checks operation after return. No agent-accessible input bridge is added to the browser. The controller now checks actions on both departure and return. A failed activation receipt cannot count as a block.

A general solution must control page activity and visibility updates without stale input state or broken browsing. AppKit key-state changes alone do not meet that requirement. These experiments remain separate from the frozen physical browser.

[Saved evidence](evidence/lifecycle-experiment-results.json) preserves hashes, positive controls, failed controls, task counts, focus logs, and cleanup. All 87 Python checks pass.
