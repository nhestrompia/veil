# Compressed HTML capture pilot

Update, milestone 123. The unchanged final H.264 protected image is black on the physical display in a fresh test. The earlier readability report is not reproducible. See [presentation findings](pixel-compositing-findings.md). Captured black images do not establish a useful visible-output defense.

Milestone 119, October 27, 2026. A new H.264 producer passes a real encode/decode check and two paired capture comparisons. The protected screenshots omit the page. The user reports a readable page on the direct physical display. No exact marker was supplied. This is not an agent-free result.

## What the Antiagent evidence established

I read the original findings, final JSON results, source audit, and protected-interface images. The retained images are present in the current checkout. The encrypted compositor image visibly contains the transfer text and capture token. The encrypted view image has a black media region. These are different capture paths, not contradictory outcomes.

The final eighteen-session matrix records these results:

| Configuration | Sessions | Compositor reads | View reads |
| --- | --- | --- | --- |
| Clear interface video | 3 | 3 | 3 |
| Two supported software Widevine levels | 6 | 6 | 0 |
| Three hardware Widevine levels | 9 | Unsupported | Unsupported |

The hardware requests stopped without software fallback. Unsupported playback did not count as protection. The fixture contained a prerecorded interface and exposed its matching clear asset. It did not implement arbitrary interactive HTML or network confidentiality.

The GPU guard also blocked six ordinary no-CDP controls and leaked a useful frame in one sparse-capture trial. The cover heuristic missed foreground captures. Those findings reject these particular detectors as capture-prevention mechanisms.

Source links: [protected interface](/Users/nhestrompia/Projects/antiagent/docs/protected-ui-findings.md), [final robustness matrix](/Users/nhestrompia/Projects/antiagent/docs/protected-output-results.json), [GPU guard](/Users/nhestrompia/Projects/antiagent/docs/gpu-pixel-guard-findings.md), and [cover findings](/Users/nhestrompia/Projects/antiagent/docs/capture-cover-findings.md). The evidence summary pins twelve reviewed source and image hashes.

## New implementation

The new pair uses the same hidden WKWebView snapshot producer. It converts HTML snapshots to NV12 and encodes them into H.264 samples. The display layer receives the encoder-produced samples directly. The protected build sets `preventsCapture`; the control does not. Neither build uses DRM encryption or a license server.

The encoder requires hardware and low-latency mode. Every property setter, frame submission, and completion result is checked. Timestamps increase. Frame drops, missing samples, wrong formats, and changed dimensions cause refusal. The renderer hides its pixel layer after a reported producer error. It has no visible clear-WebView fallback and no input bridge.

The encoder hardware-status query returns `kVTPropertyNotSupportedErr`, or -12900, on this Mac. The report preserves that unavailable readback. Hardware remains a creation requirement under Apple's API contract. The smoke check separately requires hardware decoding and confirms its readback as true. Hardware requirements do not prove capture exclusion.

## Live checks

Three different two-tone frames survive actual H.264 encoding and decoding. Their decoded brightness matches the source within the declared tolerance. Presentation timestamps advance from zero through 0.2 and 0.4 seconds. A changed frame size is refused.

Each comparison uses one fresh local page in each build:

| External route | Clear control marker | Protected marker |
| --- | --- | --- |
| ScreenCaptureKit window | Recovered | Not recovered |
| ScreenCaptureKit filtered display | Recovered | Not recovered |
| System window screenshot | Recovered | Not recovered |
| Unfiltered compositor capture | Probe refused missing owned backdrop | Same refusal |

The successful filtered-display route includes the research window only. It is not an unfiltered whole-display result. The protected images show a black page area. Readiness is true and external-obscuring state is false, but those flags do not prove physical visibility.

Both apps compile with Swift 6 and warnings as errors. Strict code signatures pass. The unchanged BGRA branch also typechecks. Python compilation passes. All five frozen permissioned binaries retain their expected hashes. No input injection, hook modification, new grant, or administrator access occurred.

## Remaining gate and reproduction

The user reports that the protected H.264 page is readable on the physical display. No exact marker was supplied. A follow-up in that same process captures a black page through all three successful routes. The earlier unavailable-window and relative-output-path errors remain in the local artifacts. Neither error counts as prevention.

Two paired comparisons ran. The final comparison pins the final app binaries. Both controls expose their markers through three routes. Neither protected page exposes its marker through those routes. The physical readability report applies to the earlier build with identical rendering code. No exact marker was supplied.

This is a promising route-specific result. Unfiltered whole-display and continuous capture, transitions, recovery, and interaction remain untested. A later correction moves negative-test allocation outside its expected-error block. It changes the smoke check and final app hashes, but not rendering code. The evidence pins both the pilot and final images. The final-image capture comparison reproduces all three results.

The computer-use tool returned after the bounded trial ended. It opened an empty app without a fixture URL. That observation is invalid, and the empty owned instance was stopped. The original test app and isolated server also exited. No test window remains.

```sh
bash scripts/build-compressed-rendering.sh
dist/PixelH264Control.app/Contents/MacOS/PixelH264Control --codec-smoke
python3 tools/run_rendering.py --targets PixelH264Control PixelH264ProtectedExperiment --repetitions 1 --controller PATH_TO_FIXTURE_CONTROLLER --output artifacts/compressed-repeat
```

The runner needs its local fixture and the unchanged probe's effective grants. Each repetition creates fresh content. The runner never upgrades missing markers into a prevention verdict.

See [saved evidence](evidence/compressed-rendering-results.json), [control image](evidence/compressed-control.png), [protected image](evidence/compressed-protected.png), [physical-session capture](evidence/compressed-physical-session-capture.png), and [primary-source producer research](research/capture-producer-options.md).
