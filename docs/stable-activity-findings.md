# Stable page activity and password input ownership

A separate diagnostic stopped the tested visibility, blur, and password-page focus actions during hide and restore. It still fails a native input ownership requirement. Its password view retained Secure Event Input while its application was hidden. This diagnostic is not enabled in the live browser.

## Exact comparisons

| Page listener | Matched readable action | Candidate action during cycle | Private task after return |
| --- | --- | --- | --- |
| Document visibilitychange | Two accepted actions | None | One accepted action |
| Window blur | One accepted action | None | One accepted action |
| Window focus with a password field | One accepted action | None | One accepted action |

Each comparison used one fresh candidate. The helper verified hidden state and return activation. It posted no keyboard or pointer input and made no candidate AX call during those cycles. Candidate gates admitted zero input events during each cycle. All private baselines and resumed tasks completed, with no HID reader running.

The diagnostic reports logical key-window, visible-window, and occlusion values that remain active. Its native logs also read the superclass state. Those logs confirm that actual key and visibility became false while the logical values stayed true. The generated keyboard router retains both actual key-window and foreground-PID checks.

## Password failure

The readable password view released Secure Event Input while hidden. The stable-activity candidate kept it enabled before hiding, while hidden, and after return. That result confirms the source coupling between WebKit's logical key state and its input ownership.

Every temporary process passed cleanup. Secure Event Input was off after each cleanup. The problem is hidden ownership during the experiment, not failed cleanup. No global input hook or permission change occurred.

WebKit source contains an owner-aware reset method. A reset on deactivation alone does not prevent a later editor update from reacquiring ownership. No independent Objective-C rearm API emerged from the bounded source review. See [the pinned source analysis](research/activity-boundary-design.md).

## Next implementation boundary

The next design must separate web-exposed activity from actual native focus. It must preserve ordinary text and password entry, release native ownership when the app loses real focus, and restore protection before resumed password input. The actual keyboard router must remain independent of any logical page state.

The host getter experiment does not meet those conditions. Keep it separate while comparing an engine boundary with alternatives. Finite fixture comparisons still do not establish compatibility or agent-free operation across all websites.

The physical browser and permissioned probes remain frozen. [Saved evidence](evidence/stable-activity-results.json) includes hashes, matched outcomes, actual and logical window logs, input counts, and cleanup.
