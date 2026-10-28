# Live continuous capture of the MVP

Milestone 140 runs the approved PreviewStreamCaptureProbe against the actual combined browser. The 30-second independent-window comparison delivers 948 complete candidate frames. Every frame passes the RGB and alpha audit. None reveals the page marker. Readable references before and after both expose their exact markers.

The app-filtered display route delivers no complete candidate frames and remains inconclusive. Missing frames do not count as black images or capture prevention. No input or AX action runs in either route. No new candidate submission occurs.

## Scope and grant

The user approves the exact helper's Screen Recording request and enables it in macOS. A fresh preflight confirms effective access. The final helper retains SHA-256 `c5dcf53813d87b6fecd6d2e042f96803ea947f4d13d402b02b0273c02cbcc79a`. No app rebuild, re-signing, permission refresh, or reset occurs.

Both comparisons use unchanged preview PID 35426 and its earlier physical completion in this same session. The browser image remains `dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70`. The fixture retains exactly one accepted submission. Physical display visibility is not observed again during the stream itself.

## Results

| Route and stage | Complete frames | Audited frames | Frames with non-black output | Marker |
| --- | --- | --- | --- | --- |
| Independent window, before reference | 956 | 956 | 956 | Recovered |
| Independent window, preview | 948 | 948 | 0 | Not recovered |
| Independent window, after reference | 954 | 954 | 954 | Recovered |
| App-filtered display, before reference | 935 | 935 | 935 | Recovered |
| App-filtered display, preview | 0 | 0 | 0 | No complete image |

The window comparison scores `all-delivered-complete-frames-black`. Each valid complete buffer has zero RGB and uniform alpha. The native recorder audits every such buffer, rather than only the saved PNG samples. The OS may drop or omit frames. This result covers delivered buffers, not every display update or possible recording API.

The display comparison stops on incomplete candidate output. It supplies no after-reference or blocking verdict. Both native streams stop successfully. Neither mode captures audio or unrelated app pixels. Window mode selects one owned window. Display mode includes only the owned research app and crops to that window.

Local image inspection agrees with the window audit. See the [black preview sample](evidence/preview-stream-black.png) and [readable reference](evidence/preview-stream-control.png).

## Failed controls and controller repair

Three earlier readable controls lose foreground focus. Their streams stop, their references close, and no protected candidate runs. One diagnostic saves a readable sample before focus loss, but does not complete the required duration. It remains failed calibration.

The ordinary controller now launches its native metadata and activation probes in the background. The first retry still fails, so this change is not established as a causal fix for the earlier focus losses. A separate reference later completes with 957 audited frames and exact marker recovery. Its metadata-only trace records no foreground change during its bounded observation period. No focus-restoration loop or synthetic input runs.

The first trace loses its report when a helper disappears between process queries. The repaired, unpermissioned trace handles that exit and retains partial observations. It reads only foreground roles, not UI content, and refuses an unrelated target. The recorder's native foreground guard remains unchanged throughout.

## Verification and remaining limits

All 17 Python checks pass, including the background-launch regression and capture scoring guards. Python compilation passes. The metadata trace compiles with Swift 6 warnings as errors. All 13 permissioned app images and browser source hashes remain unchanged. Only the ordinary Python controller and its recorded hash change.

All transient probes, traces, and references stop. Both modifier apps remain running. No global input, administrator access, or computer-use service runs. The preview and private fixture remain open under their existing one-hour watchdog.

See [saved results](evidence/preview-stream-live-results.json). The MVP stays minimal. Unfiltered capture on this exact preview, filter changes, resize/fullscreen, external inspector attachment, keyboard observation, autonomous page actions, and broad website compatibility remain open. These bounded results do not establish agent-free browsing.
