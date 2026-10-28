# Physical keyboard observation after readiness repair

An external process recognized the fixed fake phrase while the restricted browser accepted the requested physical task. Both Unicode and virtual-keycode matchers succeeded. This is a positive keyboard-observation result. The browser remains unproven as agent-free.

## Verified sample

The candidate was PID 61893. It used the same source-policy executable as the earlier physical session, but it was a new process. Its SHA256 was `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`.

The observer received sixteen key-down events with Unicode. Both fixed-phrase match flags were true. The independent oracle recorded one accepted task. Device binding and unchanged candidate identity were confirmed. The controller generated no input for this sample. The user reported completion.

The observer stopped when the target lost focus. It removed its tap and passed process cleanup. It saved counts and fixed-phrase match flags only, with no raw text or key codes. This demonstrates recognition of the known test phrase. It does not demonstrate arbitrary text extraction, a page-marker disclosure, or an autonomous website action.

The [saved physical result](evidence/keyboard-readiness-physical-results.json) preserves these limits. The [generated reference](evidence/keyboard-readiness-generated-results.json) completed one task and matched both decoders from thirteen events. That reference is explicitly generated, not physical. Consequently, `referenceDecoderCalibrated` remains false for a physical comparison. This limits negative claims but does not erase the positive candidate observation.

## Readiness and collection repairs

The observer now signals an enabled tap from its running event loop. Controllers wait for that signal before input or target activation. Process liveness alone no longer establishes readiness.

The PID-scoped listener allows five seconds for target focus. It then waits up to sixty seconds for the first key without decoding text. That first key starts the fifteen-second sample. Focus loss ends collection. A monotonic state machine covers these transitions.

An independent `permissions` command checks existing grants without a target PID, monitor, or consent request. The signed observer remained frozen after its approved app-only Accessibility reset and exact-bundle Add restored effective access.

The observer SHA256 was `cdd1829e60dd838f5a2b1ef91f9d5635e7f61760360f9c18c494f8eb90086aac`. NativeProbe remained `7c256598528dcaf2dcdc6437af30dab92d9c4ca929a55a3a2402f09754f67de1`.

## Validation and next experiment

All 66 Python checks pass. Swift checks cover the fixed matcher and observation timing. The observer compiles with warnings as errors. No modifying tap or device seizure was used.

The next bounded comparison tests ordinary text and password fields. Apple documents Secure Event Input for sensitive entry and advises against general-text or application-lifetime use. See [Apple TN2150](https://developer.apple.com/library/archive/technotes/tn2150/_index.html). Existing WebKit source enables secure input for focused password fields. That source does not establish the installed runtime result.
