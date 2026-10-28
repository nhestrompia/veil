# Compositor layout update

Milestone 143 installs the reviewed PreviewCompositorProbe update after explicit user approval. Its app-only Screen Recording refresh succeeds after off/on, re-add, reset, and a final re-add. A fresh process reports effective access. The browser image stays unchanged. No candidate capture runs.

## Layout change and evidence

Three metadata-only controls compare nonactivating panels in a fullscreen Space. Normal-level placement and orderBack fail. Placement at level minus one passes the coverage check after a 500-millisecond wait. The target stays in front of the opaque owned panel. Only the target intersects the measured crop above that panel.

The staged update changes exactly three lines in the original recorder source. It uses the new panel factory and checks the panel's exact level. All target ownership, opacity, foreground, crop, overlap, and cleanup checks remain. The two allowed targets, capture filters, no-input/no-audio scope, and 25-second alarm stay unchanged.

The builder stages the candidate and saves the original signed app before installation. The reviewed image hash is 2ce201a2876e295fe6695fbda6506b72e1d9ac706f6051226377f5a8fa3f4a2b. The old image remains in artifacts/preview-compositor-143/recorder-update/original. Do not rebuild or re-sign the granted image. The manifest also pins the generated source in .build/diagnostics/PreviewCompositorPanelProbe.swift. Preserve that file.

## Grant refresh

The initial installation attempt requires explicit approval because it replaces a permissioned image. The user approves the reviewed update and the complete app-only refresh sequence. Off/on and re-add leave effective access false. The approved reset affects only ScreenCapture for research.agentfreebrowser.previewcompositor. The final re-add shows the exact switch on. A fresh native preflight reports true. No authentication prompt appears during the final re-add.

## Readable calibration still fails

The first updated-recorder control loses foreground focus before capture. The second retains focus but fails the overlap check. Both return no saved images and close their reference and fixture. Neither result establishes capture prevention.

A metadata-only focus trace observes only the research-target role during the second control. A separate layout trace samples eleven times over one second. It sees an additional window throughout. The window belongs to UserNotificationCenter, at layer eight, within the crop. This explains that trace's overlap refusal. It does not prove what caused the earlier trial's focus loss.

The timing trace also sees no backdrop in its first sample. The backdrop appears by the next sample. This suggests asynchronous window placement, but the unrelated overlap prevents a successful timing control. Do not remove the overlap guard or infer successful capture from the earlier metadata-only pass.

Automatic approval review rejects inspection of UserNotificationCenter because it can expose unrelated private notifications. No alternate inspection route runs. The user is away. Leave that alert untouched and continue independent work. No unrelated app closes and no global setting changes.

## Checks and next steps

All 29 Python checks pass. Swift 6 compilation with warnings as errors and strict signature checks pass. Seven image manifests match their binaries, including the unchanged preview and updated recorder. All nine recorded browser source files match their committed versions. All research references, fixtures, and transient helpers stop.

The calibration command now supports a bounded setup phase:

```sh
PYTHONPATH=tools python3 tools/calibrate_preview_compositor.py \
  --output artifacts/FRESH --wait-for-setup
```

It writes ready.json and waits at most 60 seconds. After fullscreen setup, create setup-complete in that directory. A stop file takes precedence. Timeout stops the trial without capture and closes its resources.

Resume readable calibration after the unrelated alert leaves the crop. Require marker recovery in all three filter stages before testing a candidate. A candidate comparison also needs a fresh physical completion on the same process. No current physical preview exists. The prior session expired. Agent-free acceptance remains unmet.

See the [saved results](evidence/preview-compositor-layout-update-results.json) and [permission manifest](evidence/preview-compositor-permission-manifest.json).
