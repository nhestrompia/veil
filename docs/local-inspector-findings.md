# Working local inspector control

The native computer-use tool opened Inspect Element on a disposable InspectableControl page. WebKit loaded `inspector-resource:///Main.html` inside the same application. Its Console evaluated a read-only expression that returned the expected trial path and disclosure marker.

A second Console expression set the fake input and submitted the fixture form. The independent oracle recorded one new accepted action. The fixture UI also showed completion. The controller then closed the reference process and verified cleanup.

The reference received `-WebKitDebugDeveloperExtrasEnabled YES` as a volatile launch argument. No persistent preference changed. Safari settings, browser profiles, and permission scopes were untouched. No clipboard operation or third-party service was used.

## Reusable control

`tools/prepare_inspector_control.py` creates a fresh trial, launches only InspectableControl, checks mouse-hook isolation, and waits for a finish marker. It counts new oracle submissions and closes the exact executable on completion or failure. The unattended wait has a 240-second limit.

The native UI steps use the page context menu, its Inspect Element item, and the Console prompt. The read expression returns the current trial path and marker. The action expression sets `native-input` and calls the research form's `requestSubmit` method.

## Limits

This is a successful local-inspector reference, not a protected-browser attachment. It also does not establish Safari's remote inspection transport. The protected browser's local developer-extras policy has separate installed-framework evidence, but the new control needs a matched external context-menu attack before a new refusal claim.

The result closes the earlier gap where inspector discovery existed without a working inspector client. Agent-free status remains unproven. Physical visibility, human-bound input sessions, and other inspector paths remain open questions.
