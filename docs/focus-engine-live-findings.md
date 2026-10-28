# Live MVP tests of the engine browser

Milestone 153 validates physical text entry and repeats external attacks on the same public browser process. The focus defense passes its live repeat. A global key-code attack also fails after its readable reference succeeds. This extends the diagnostic results with actual human use.

## Exact browser and human controls

AgentFreeBrowserEngine runs as PID 2082 with SHA-256 `12de797fbbfea6f5536b13b8ba890354170f3561f681620bb49be42f2fdf7e21`. The user completes the local task with the built-in keyboard and leaves the window untouched. After the focus and observation trials, the user reports that the page remains visible and completes the task again. The independent fixture records two accepted actions in total. The later native input trials add none.

The user approves this app's separate Input Monitoring request. The first command-line launch reports access off. App-specific macOS diagnostics attribute that launch to T3 Code. Adding the exact app in Settings, then launching through LaunchServices, reports access on. The repaired launcher preserves native app attribution. No browser rebuild or signature change occurs. Commit ttq contains this launch repair and the approved grant record.

## Live results

| Method | Readable control | Same browser result |
| --- | --- | --- |
| Three focus cycles | Three native-engine cycles each cause an action | Zero new actions and zero admitted input |
| Host Accessibility read | Before and after recover each fresh marker | No page marker in the bounded tree |
| Accessibility form action | Before and after complete the task | Fixture controls absent, no new action |
| Independent-window snapshot | Before and after recover each marker | Image returned, no marker recovered |
| Window-inclusion display snapshot | Before and after recover each marker | Image returned, no marker recovered |
| System window screenshot | Before and after recover each marker | Screenshot command fails, remains inconclusive |
| Global HID-source key codes | Fresh reference completes the task | Zero admitted events, 29 refusals, no new action |
| Directed-window key codes | Fresh reference does not complete | Candidate skipped, remains inconclusive |
| Native computer-use binding | No new matched client control | Client returns `Computer Use server error -10005: timeoutReached` |

The focus attack uses the completed native-engine reference from milestone 152. Its content-process mapping check confirms the expected WebKit, WebCore, and JavaScriptCore images in the actual browser session. Stationary controls record no new action. The agent sends no keyboard or mouse input during those cycles.

The screenshot images are window-scoped. The display snapshot includes the target window only. Neither is an unfiltered display result. Local inspection finds black candidate output. The [candidate sample](evidence/focus-engine-live-black.png) and [readable reference](evidence/focus-engine-live-control.png) belong to this new build.

The native posting phases temporarily pause the two previously approved mouse utilities. The safety guard remains active. Both phases verify that the probe stops before restoring LinearMouse and DockDoor. A failed reference never counts as a browser defense. Refusal counts can include ambient events, so they do not identify every posted event.

## Next capture experiment

A new EngineCompositorProbe is built for only this exact browser and InspectableControl. The old granted recorder remains unchanged. The new final helper has SHA-256 `3186515e7a0ac3e52681f485b0047f0f8dcec2a4ef7f8b3f6d3a9e16458d6fe4`. It has no approved or effective Screen Recording grant. Its direct permission-request command is unavailable. Both the runner and native helper refuse a capture sequence before approval for the exact helper image.

An earlier ungranted helper image runs metadata-only coverage. It refuses another window inside the research crop before any capture. Its backdrop and helper close. Do not inspect that window or remove the coverage guard. The physical crop must be clear before the final helper can run a valid comparison.

The planned sequence switches from unfiltered display to owned apps, then back to unfiltered display. It keeps the opaque owned backdrop, foreground, ownership, geometry, overlap, and 25-second checks. It captures no audio and sends no input. Complete frame auditing remains required for a protection result. A marker in a saved partial recording still counts as disclosure. The approval checks control this workflow, not OS security.

## Evidence and acceptance

The [result file](evidence/focus-engine-live-results.json) preserves the controls, exact image, grants, oracle states, earlier inconclusive results, hashes, and current session state. Fifty relevant Python tests pass. All 14 frozen research images retain their hashes. All transient helpers and readable references stop. The browser and private fixture remain open under their one-hour watchdog for the next test.

The minimal app now has a physical text control and a live focus-defense result. Physical password input, unfiltered recording, external inspector scripting, renderer reads on this new identity, broader compatibility, and distribution hardening remain acceptance work. Existing public-site results apply to the older preview. The current tests support these measured outcomes, not an agent-free guarantee across all tools and websites.
