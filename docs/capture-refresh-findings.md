# Capture-filter refresh probe

Milestone 126 prepares an external stream attack against the readable window-sharing diagnostic. Live capture remains pending. The final helper reports Screen Recording off through LaunchServices. No permission request occurs.

The helper opens one ScreenCaptureKit stream. It changes from a display filter including the owned window, to an owned-app filter, then back to the window filter. It excludes the app's other existing windows from the app filter. No filter includes unrelated apps or an unfiltered display. It captures no audio and sends no input.

The helper checks the exact diagnostic bundle identifier, executable path, recorded executable hash, process launch date, window owner, ordinary window level, and stable window bounds. The target must fit on one display. The helper refuses output outside this project's artifacts directory and refuses an existing report. A native alarm bounds it to 30 seconds.

Each stage lasts two seconds and saves up to eight sampled complete frames. A missing frame is inconclusive. Frames queued around an update can cross stage boundaries. This probe does not establish continuous capture exclusion. It also does not reproduce the unfiltered-display configuration from the [Apple forum report](https://developer.apple.com/forums/thread/808016). That route needs its own safe coverage control.

## Verification

Swift 6 compilation with warnings as errors and strict signature checks pass. Shell syntax and Python compilation pass. Six refusal checks cover an unknown command, unrelated process, malformed window, malformed hash, output scope, and an existing report. A real owned control passes identity checks and refuses absent Screen Recording before capture starts. Its host and fixture server stop. These are eight passing checks on the final executable. Streaming and filter updates remain unexecuted.

An earlier preflight crashes because Foundation rejects combining atomic and without-overwriting write options. The repaired helper uses without-overwriting alone. All final checks use that repaired executable.

The [permission manifest](evidence/capture-refresh-permission-manifest.json) pins the executable and source. The build script refuses to rebuild that pinned identity. The [preflight results](evidence/capture-refresh-preflight-results.json) record no new grant. All seven earlier permissioned images retain their hashes.

## Live sequence after separate consent

The prepared permission command appears in the manifest. It must not run before the user approves this helper's Screen Recording request. macOS grants broad screen access. This helper's capture code limits itself to the exact disposable research app.

Build an ordinary restricted diagnostic with scripts/diagnose-browser-keyboard.sh using --capture-restricted --physical-window-session --build-only. Start tools/run_window_capture_session.py with --window-only and a fresh artifact directory. Then run tools/run_capture_refresh_probe.py with --session pointing to that session.json and --output pointing to a new artifact directory. Repeat with the clear ordinary diagnostic after stopping the first session. The runner refuses a changed target image or stale session.

Use the existing physical visibility result only for the same rendering configuration. A changed presentation needs a fresh physical check. Score marker recovery against the clear reference. Keep untested transitions and capture routes open. No agent-free claim follows from probe preparation.
