# Continuous-capture preparation for the MVP

Milestone 139 keeps the user-confirmed [minimal MVP scope](mvp-scope.md). No tabs, bookmarks, browsing-history UI, or replacement browser app is built. The existing combined preview remains unchanged and physically completed as PID 35426.

The new PreviewStreamCaptureProbe prepares 30-second capture tests of that actual app. It has no Screen Recording access. No permission request or continuous stream runs in this milestone. Its final image is pinned before its first non-prompting trust query, which reports access false.

## Scope and capture modes

The helper accepts only the hash-pinned AgentFreeBrowserPreview and InspectableControl. It reuses the unchanged process-identity policy from the renderer probe. It checks the host's executable, process start time, user identity, foreground state, and stable owned window geometry. Existing helper scopes do not expand.

Window mode uses one desktop-independent owned window. Display mode includes only the exact research app and crops to its window. Both exclude the menu bar and cursor. Neither mode captures unrelated app pixels, adds audio output, posts input, or installs hooks. These are filtered capture routes. Unfiltered whole-display capture remains separate.

Each invocation runs for 30 seconds with a 45-second native alarm. The callback audits every valid complete frame delivered by ScreenCaptureKit. It checks every RGB pixel and requires uniform alpha within each frame. This catches alpha masks as possible output as well as visible color. Unsupported buffers remain unaudited and prevent a passing result.

The helper retains at most 16 sampled images plus the first frame with non-black RGB or nonuniform alpha. Idle statuses are distinct from complete frames. Missing frames are inconclusive. Configured frame rate does not prove that the OS delivers every display update. Filter changes, resizing, fullscreen, multiple displays, and other capture APIs remain untested by this helper.

The comparison runner requires the exact live physical declaration and image. Each route needs fresh readable references before and after the candidate. Both references must recover their own marker. Every reported complete candidate frame must pass the pixel audit for an all-black result. Non-black output without a recovered marker gets a separate result. No global input or modifier-app pause is needed.

## Available live screenshot check

The already-permissioned NativeProbe tests macOS's window-screenshot command on the same physical session. Its fresh readable reference exposes the exact marker. The preview's screenshot command returns System capture failed. That candidate result remains inconclusive. It is not a black-image result or a prevention claim.

The readable reference stops, the preview regains focus, and no new candidate submission occurs. This test uses no new grant or input event. Full records remain in `artifacts/preview-stream-139/system-window/`.

## Checks and next step

Twelve Swift pixel-audit checks and 16 Python checks pass. The tests include alpha masks, row padding, truncated buffers, missing and unaudited frames, short streams, failed reference calibration, disclosure scoring, failed cleanup, and permission guards. Swift 6 compilation treats warnings as errors. Strict signature checks and Python compilation pass.

The final new helper SHA-256 is `c5dcf53813d87b6fecd6d2e042f96803ea947f4d13d402b02b0273c02cbcc79a`. All 12 existing permissioned images and the browser sources retain their hashes. All transient helpers and references stop. The physical preview and fixture remain live under their existing watchdog.

The next step needs separate approval for this helper's Screen Recording request. That broad macOS permission is new for this app. Its code limits capture to the two pinned research apps. The exact request remains unexecuted in the [permission manifest](evidence/preview-stream-permission-manifest.json). Do not rebuild or re-sign this image before or after consent.

See [saved preparation results](evidence/preview-stream-preparation-results.json). This milestone establishes neither continuous-capture prevention nor agent-free browsing.
