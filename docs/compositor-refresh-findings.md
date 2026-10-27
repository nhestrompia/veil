# Unfiltered stream refresh preparation

Milestone 129 prepares CompositorRefreshProbe for the remaining exclusion-toggle attack. The existing frozen NativeProbe captures an unfiltered screenshot or first stream frame. CaptureRefreshProbe updates only inclusion filters. Neither can run the [Apple forum report's exclusion-toggle sequence](https://developer.apple.com/forums/thread/808016).

The new helper starts a display stream that excludes itself. It then excludes no apps, then excludes itself again. The target and opaque backdrop remain included throughout. A small noninteractive helper indicator sits outside the crop so the helper has a discoverable application identity. The helper refuses any indicator overlap with the capture region.

Every capture uses a crop inside the target and its owned backdrop. The helper checks the exact research bundle, executable path, recorded image hash, process launch date, foreground state, window ownership, ordering, opacity, stable bounds, backdrop window level, backdrop sharing state, and intersecting overlays. It checks coverage before each stage, before saving each sampled image, and after each stage. It records no unrelated app names.

The stream registers only screen output and disables audio. It posts no input and installs no hooks. Each stage lasts two seconds and saves up to eight sampled complete frames. A native alarm bounds the helper to 30 seconds. Output must be a new file inside project artifacts.

Coverage checks and frame acquisition are not atomic. Queued frames can cross an update boundary. The sample limit does not establish continuous exclusion. The experiment does not test QuickTime, fullscreen, resizing, every capture API, or external input.

## Verification before consent

Thirteen final preflight checks pass. They cover malformed requests, an unrelated process, equal window identifiers, output scope, overwrite refusal, valid geometry, a wrong owned-image hash, an unowned backdrop, absent permission, an undersized backdrop, and cleanup of both owned controls. No preflight captures pixels or requests a grant. The runner also refuses missing permission before launching its browser control.

The first unapproved candidate refuses valid geometry because macOS redacts its backdrop sharing state without Screen Recording. A comparison from milestone 128 shows zero for the ungranted metadata reader and one for the granted reader. The repaired metadata-only coverage mode checks geometry without making a sharing-state claim. Live capture still requires the backdrop to be shareable. The original unapproved candidate and failure remain in artifacts.

The [permission manifest](evidence/compositor-refresh-permission-manifest.json) pins the final executable and source. The builder refuses to rebuild this pinned identity. Swift 6 compilation with warnings as errors, strict signature verification, Python compilation, and shell syntax pass. All existing granted images remain unchanged. The final LaunchServices preflight reports Screen Recording off. No request is approved or issued for this new helper.

## Prepared live run

After separate approval, execute the exact permission request in the manifest through LaunchServices. Keep the helper unchanged during consent and testing.

Build the metadata tool with scripts/build-owned-window-metadata.sh. Run tools/run_backdrop_metadata.py with --variant compact --use-physical-archive --compositor-refresh and a fresh artifact directory. Use --restricted for the candidate. Run clear, restricted, then clear again. The controller restores the archived physical-test executable and verifies its original bundle signature without re-signing. It stops its own host and fixture after each trial.

See [preflight results](evidence/compositor-refresh-preflight-results.json). No live filter-refresh result follows from this preparation, and agent-free browsing remains unproven.
