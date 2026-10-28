# Readable window under unfiltered display capture

Milestone 128 tests an unfiltered display filter with a crop inside verified research coverage. The exact archived restricted executable is the compact-backdrop image the user reports as readable in milestone 125. Its original bundle signature verifies without re-signing.

The frozen NativeProbe checks opaque coverage, window ownership, ordering, foreground state, and intersecting overlays before and after capture. The filter excludes no windows. Its crop remains inside the target and its owned backdrop. The experiment captures no unrelated app content.

| Route | Clear before | Restricted trial | Clear after |
| --- | --- | --- | --- |
| Unfiltered compositor screenshot | Page marker recovered | Only owned backdrop, marker absent | Page marker recovered |
| First complete frame from an unfiltered stream | Page marker recovered | Only owned backdrop, marker absent | Page marker recovered |

The agent visually checks the readable screenshot and the restricted screenshot. The latter contains the controlled backdrop label on teal, rather than a failed or empty image. Both restricted routes return real images, and all six captures pass the frozen coverage guard. No restricted page marker is recovered.

## Earlier availability failure

The milestone-125 compact controls returned no onscreen window metadata and failed the adapter's availability check. That failure does not reproduce now. A separate read-only tool finds both owned windows onscreen. The frozen reader agrees. The first metadata trial captures no pixels and confirms that the new tool has no Screen Recording grant.

This does not establish the cause of the earlier failure. No capture helper, coverage guard, permission, or backdrop layout changes to restore calibration. The new metadata tool filters for the exact research process and executable hash before it emits window data. An unrelated-target check refuses before enumeration.

## Controls and limits

The restricted trial and final clear control restore archived executables and verify their original signatures. The initial clear reference uses a fresh build of the same diagnostic configuration. Each host completes one fixed local task through process-local keys. No device reader starts and no synthetic system input is posted. This is not a physical input control or an external action defense.

The restricted physical report is user-declared, without an exact marker. It refers to the exact archived executable, but to an earlier launch. This result covers one screenshot and one first complete stream frame per flavor. It does not cover filter updates on an unfiltered stream, long recordings, resizing, fullscreen, QuickTime, or every capture API.

Apple exposes separate display and window filter types. Its [shareable-content API](https://developer.apple.com/documentation/screencapturekit/scshareablecontent/getexcludingdesktopwindows(_:onscreenwindowsonly:completionhandler:)) selects windows by the requested visibility criteria. Metadata availability therefore remains a separate calibration check. The [forum report](https://developer.apple.com/forums/thread/808016) about unfiltered filter changes remains an untested attack lead here.

All four owned hosts and fixture servers stop. Independent process checks verify cleanup. Seven earlier permissioned images and CaptureRefreshProbe retain their hashes. Swift 6 compilation with warnings as errors, Python compilation, and shell syntax pass. No new grant, administrator access, or input hook occurs. See [saved results](evidence/readable-unfiltered-results.json).
