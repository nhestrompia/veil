# Effective grant and compositor calibration

Milestone 142 enables the approved Screen Recording switch through the existing native UI connection. The frozen PreviewCompositorProbe confirms effective access. No new permission request, reset, authentication, native image change, or browser change occurs.

The first command-line attempt used System Events and failed in milestone 141. That failure did not cover the separate native UI path. The current connection reads the exact Settings switch, enables it, and reads back on. A fresh helper process confirms the grant. No other switch changes.

## Working calibration command

The new standalone calibration command starts one disposable readable reference and its private loopback fixture. It needs no physical-browser session. It closes both resources after failure. It never launches a protected candidate.

```sh
PYTHONPATH=tools python3 tools/calibrate_preview_compositor.py --output artifacts/fresh-compositor-calibration
```

With effective access, this command reproduces the existing overlap refusal. The native guard detects the full-display Dock window above the target and owned backdrop. No stream starts. Permission failure no longer explains this result.

## Fullscreen diagnosis and controller fix

A temporary fullscreen control owns small titlebar and sharing-status windows in addition to its main content window. The ordinary controller counts them as multiple content windows and stops before invoking the native helper. A regression test reproduces this failure before the fix.

The controller now selects an opaque, normal-level window within the native helper's existing content-size limits. It still requires exactly one such window. Two full-size windows remain ambiguous and receive no capture attempt. The regression passes after this change. The manifest records the ordinary controller's old and new hashes. The signed helper and its overlap guard stay unchanged.

The corrected fullscreen trial reaches the native helper, but its backdrop does not satisfy the ordering check in that Space. No stream starts. A separate metadata-only diagnostic tries ordinary placement, fullscreen joining, and joining all Spaces. All fail the same frozen ordering guard. These results establish no capture prevention and no successful layout repair.

Apple documents eligibility for joining another app's fullscreen Space. That API does not guarantee placement beneath this reference. The local trials remain the evidence for this setup. [Apple window behavior](https://developer.apple.com/documentation/appkit/nswindow/collectionbehavior-swift.struct/canjoinallapplications).

## Verification and limits

All 26 Python checks pass. They cover fullscreen selection, refusal of ambiguous windows, missing grants, and fixture cleanup after capture failure. Python compilation passes. All fourteen signed research images and browser source hashes remain unchanged. All five readable references, private fixtures, and temporary probes stop.

No protected browser starts. No physical completion is invented or transferred from the expired session. No NativeProbe input adapter or administrator action runs. Native UI actions enable the approved switch and enter fullscreen on four disposable references. The service already runs before connection.

The approved grant remains effective for the unchanged recorder. Unfiltered capture still lacks a successful readable calibration under the current coverage rules. Enabling permission does not resolve that separate design problem. External inspection, keyboard observation, autonomous page actions, and broader human use also remain open.

See [saved results](evidence/preview-compositor-grant-calibration-results.json). The combined MVP remains available as an artifact. Agent-free acceptance remains unmet.
