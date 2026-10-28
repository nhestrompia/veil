# Unfiltered compositor probe preparation

Milestone 142 later confirms effective access and runs further calibration. See [current findings](preview-compositor-grant-findings.md). The sections below preserve milestone 141.

Milestone 141 prepares a separate recorder for unfiltered display capture and live filter changes on the unchanged MVP. No compositor recording runs. Two metadata-only readable controls fail the coverage check. Missing permission and failed controls remain inconclusive.

## Test design

The new PreviewCompositorProbe accepts only the fixed, hash-pinned AgentFreeBrowserPreview and InspectableControl images. It puts an opaque temporary backdrop behind the target at normal window level. It sends no input and installs no hooks. The backdrop closes on exit.

The crop stays inside the target and backdrop. Metadata checks require stable ownership, process start identity, foreground state, geometry, opacity, and ordering. Another intersecting window causes refusal. These checks are not atomic with frame production. They cannot guarantee isolation during a concurrent desktop change.

The planned sequence changes from unfiltered display capture to the two owned apps, then returns to unfiltered display capture. Each stage lasts at least three seconds. The stream audits every delivered complete BGRA buffer for spatial differences across all four channels. Alpha-only differences fail the uniform-output condition. Uniform color changes over time are not a tested defense against timing channels.

The controller requires exact marker recovery in every stage of readable controls before and after the candidate. Missing frames, incomplete audits, missing controls, and failed shutdown remain inconclusive. Nonuniform output without marker recovery remains a separate result. It cannot pass as uniform output. Queued frames around filter changes remain a timing limit.

Apple documents display filters and window ordering. The plan uses those APIs but makes no prevention claim from their configuration. [ScreenCaptureKit filters](https://developer.apple.com/documentation/screencapturekit/sccontentfilter), [window ordering](https://developer.apple.com/documentation/appkit/nswindow/order(_:relativeto:)).

## Measured preparation

The helper compiles with Swift 6 warnings as errors and has a valid strict signature. Its final SHA-256 is `78a3fba76544384970a008b1e32b7da9ca13a1178f5acf05861500c09a236642`. Its manifest pins the final image before the first permission query. The builder now refuses replacement. Preserve this image.

All 22 Python checks pass. Four Swift Testing tests pass with twelve total invocations. These include RGB differences, alpha differences, row padding, invalid dimensions, incomplete streams, failed controls, filter order, cleanup, and refusal of implicit permission requests. The initial SwiftPM run fails because its default module cache is outside the sandbox. The test script now puts its caches inside the project, and the rerun passes.

Both readable placement checks refuse an intersecting window. A bounded metadata trace identifies a full-display Dock window above the target and backdrop. The overlay has layer 20, alpha 1, and sharing state zero. This does not establish its actual pixels or opacity. No screenshot reads it. The native guard remains intact, and no capture starts. An unrelated process also receives an explicit refusal.

## Grant and session state

The user approves this exact helper's Screen Recording request. The request runs, but a fresh preflight still reports access false. The user is away from the keyboard and asks for automatic enablement. The scoped System Events attempt fails with error -25211, because osascript lacks assistive access. No setting changes, authentication, permission reset, or computer-use service start occurs.

The previous physical preview reaches its original one-hour watchdog limit and stops with its private fixture. Its physical completion does not transfer to a replacement. No new preview starts. All temporary references and probes stop. All thirteen earlier permissioned images and browser source hashes remain unchanged.

See [saved evidence](evidence/preview-compositor-preparation-results.json) and the [permission manifest](evidence/preview-compositor-permission-manifest.json). Enabling the grant alone does not complete this experiment. The readable coverage failure also needs resolution. A later candidate test needs a new physically completed session of the unchanged preview. Agent-free acceptance remains unmet.
