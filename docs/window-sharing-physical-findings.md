# Physically readable window-sharing comparison

Milestone 125 pairs physical webpage visibility with scoped external capture. The ordinary restricted diagnostic uses window sharing set to none. It uses no protected media. The user reports "visible" on the Mac's display. No exact physical marker was supplied.

The same process and executable remain in place for the captures after that report. The agent visually inspects the black window image and the readable reference image.

| Route | Restricted ordinary window | Clear ordinary reference |
| --- | --- | --- |
| ScreenCaptureKit independent window screenshot | Black, marker absent | Exact marker recovered |
| ScreenCaptureKit display screenshot including only the target window | Black, marker absent | Exact marker recovered |
| System window screenshot | Capture fails, inconclusive | Exact marker recovered |

This is a useful result for two screenshot routes on macOS 26.6. A failed screenshot does not prove exclusion. The comparison does not establish general capture prevention, stream privacy, or agent-free browsing.

The high-level compact-backdrop trial is inconclusive. Both its clear reference and restricted candidate fail the frozen adapter's window-availability check. Neither unfiltered compositor capture nor stream capture contributes a blocking result.

The diagnostic completes one fixed local task through process-local keys. It starts no device reader and posts no system input. This checks page functionality only. It is not a physical typing baseline or an external input attack. The current diagnostic image in dist is the clear ordinary reference. Each session archives its actual tested executable.

All four hosts and fixture servers stop. Independent process reads find none of the four recorded host identifiers. All seven frozen permissioned images retain their hashes. Shell syntax, Python compilation, Swift 6 compilation with warnings as errors, and strict signature checks pass. No grant, administrator access, input hook, or unrelated process changes.

## Next attack

An [Apple Developer Forums report](https://developer.apple.com/forums/thread/808016) describes a sharing-none window appearing after a ScreenCaptureKit filter change. The author also reports capture through QuickTime. Apple DTS requests a bug report. These are attack leads, not reproduced bypasses in this project.

The next scoped probe must keep one stream open and change between filters that include only the owned diagnostic window or its app. The frozen NativeProbe cannot perform this update and must remain unchanged. A new helper will need its own Screen Recording approval. A read-only preflight reports no access for the ordinary command environment.

See [saved results](evidence/window-sharing-physical-results.json). Private fixture keys and expected marker values remain outside the committed report.
