# Capture-type and longer-stream preparation

Milestone 131 prepares CaptureStressProbe for two remaining screenshot attacks. No live capture or permission request occurs. Its fresh LaunchServices preflight reports Screen Recording off.

| Mode | Sequence | Saved sample limit |
| --- | --- | --- |
| sequence | Display for 2 seconds, independent owned window for 2 seconds, display for 10 seconds | 16, 16, 32 |
| steady | Display for 30 seconds | 64 |

A 60-second native alarm bounds each helper process. Samples are spread across each stage. The helper captures no audio, sends no input, and installs no hooks. It accepts only the exact InternalKeyboardControl executable, its recorded hash, and owned window identifiers.

## Why a separate test

The [Apple forum report](https://developer.apple.com/forums/thread/808016) describes two possible ways to expose a restricted window. Milestone 130 tests helper exclusion changes. Capture-type changes remain untested.

[Apple's capture sample](https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-in-macos) uses an independent-window filter for window capture. It updates both configuration and filter on a running stream. This helper tests that distinction without changing either granted capture helper.

The new helper preserves the owned crop during intermediate updates. It first enters the owned-window filter, then applies a full-window configuration. On return, it restores the narrow display crop before the display filter. This order differs from Apple's sample. The test therefore does not reproduce every possible update order. An independent-window filter contains only the owned target. Display capture stays inside the opaque owned backdrop.

The helper keeps the previous checks for identity, launch date, foreground state, ownership, stable bounds, opacity, ordering, sharing state, and overlays. Metadata-only geometry checks make no claim about backdrop shareability without a grant. Live capture requires a shareable backdrop. Queued frames and non-atomic checks remain limits.

## Preparation checks

Thirteen checks pass. They cover command and hash validation, unrelated process and backdrop refusal, equal window identifiers, valid owned geometry, missing permission in both capture modes, output scope, overwrite refusal, the runner's consent gate, and the previous comparison's scorer. The three milestone 130 scores remain identical after the scorer accepts explicit stage names.

The first direct-launch geometry control fails because owned target metadata is unavailable. Its log also records a foreground change. That result does not establish a cause or a protection success. A fresh control through LaunchServices passes geometry. Both hosts and fixture servers stop. No test captures pixels or requests a grant.

Swift 6 compilation with warnings as errors, strict signature verification, Python compilation, and shell syntax pass. All nine earlier granted images retain their hashes. The [permission manifest](evidence/capture-stress-permission-manifest.json) pins the new source and executable. Its builder refuses to rebuild the pinned identity.

## Live comparison after consent

The user must approve the new helper's separate Screen Recording request. Existing helper grants do not cover this identity. No reset or administrator access is needed.

The runner is `tools/run_capture_stress.py`. Use `--mode sequence` or `--mode steady` and a fresh absolute `--output` directory inside project artifacts. It compares archived clear, restricted, then clear images. It checks consent and effective access before host launch. Readable references and stream shutdown are mandatory. Missing candidate frames remain inconclusive.

See [preflight results](evidence/capture-stress-preflight-results.json). These preparation checks do not establish screenshot protection. Agent-free browsing remains unproven.
