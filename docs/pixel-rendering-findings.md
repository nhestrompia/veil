# Protected HTML pixels

Status: matched capture pilots ran. The protected BGRA build failed physical visibility while its control remained visible. The protected NV12 build also failed its direct-display check. See the [route calibration](route-calibration.md).

The candidate uses the public `AVSampleBufferDisplayLayer.preventsCapture` property. Apple describes this property as protection for image data against capture. This is a different mechanism from the encrypted overlay in Antiagent. See the [API research](research/remaining-boundaries.md).

## Implementation

`PixelControl.app` and `PixelProtectedExperiment.app` use the same HTML producer. Only the protected build sets `preventsCapture` to true. The flag is a compile-time choice.

A nonpersistent WKWebView loads an HTTPS page or a loopback fixture. It lives in a source window that never enters the onscreen window list. The producer takes snapshots inside the app. It converts each snapshot into an IOSurface-backed pixel buffer, then a media sample. The visible window contains the sample-buffer layer and a status label. It contains no visible clear WKWebView beneath that layer.

The source window and WKWebView hide their accessibility content. That setting still needs external tests. Clear pixel buffers exist inside the producer process. This design does not establish protection against every method that shares or reads graphics buffers.

The producer refreshes after each snapshot and a 200 ms delay. It stops after a rendering error. It never falls back to a visible clear WebView. No input bridge, address bar, navigation controls, or arbitrary-site compatibility result exists in these apps. They are rendering experiments, not replacement browsers.

## Verification

Both apps compile with Swift 6 and warnings treated as errors. Both pass strict signature checks.

A rendering-only smoke check loaded a fresh loopback trial into `PixelControl.app`. The app submitted its first sample, and the renderer reported status `1`, or rendering. This checks the snapshot-to-sample pipeline. It does not prove physical visibility or capture exclusion.

The initial console preflight refused reported locks. Later working native controls contradicted that blanket veto. The runner now records the flag as advisory context. Failed controls and invisible physical output never count as useful protection.

## Capture runner

The runner generates fresh fixture content for each protected and control trial. The external probe uses ScreenCaptureKit, system window capture, OCR, and AX traversal. It never calls the producer's snapshot method. It records any exact marker recovery as a bypass. A missing marker remains inconclusive until human visibility and matched controls exist.

```sh
bash scripts/build-rendering.sh
python3 tools/run_rendering.py --repetitions 3 --output artifacts/pixel-rendering
```

The runner requires the fixture server, effective probe grants, and working controls. It tests window capture, filtered display capture, system screenshots, and AX. Continuous capture, resize, fullscreen, transitions, and alternate buffer reads remain required if a physically visible candidate survives.

`PixelNV12Control.app` and `PixelNV12ProtectedExperiment.app` convert the same HTML snapshots through VTPixelTransferSession before display. Their first capture pilot recovered the control marker on all three routes and no protected marker. Both layers reported ready=true and obscured=false. The user reported black NV12 output on the direct display. Those flags do not prove physical visibility. Both uncompressed protected configurations fail the usability requirement on this machine.

```sh
python3 tools/run_rendering.py --targets PixelNV12Control PixelNV12ProtectedExperiment --repetitions 3 --output artifacts/nv12-rendering
```

Input resistance remains independent. Even successful capture exclusion would leave known-layout input attacks to solve. The default browser's previous native and vision bypasses still stand.
