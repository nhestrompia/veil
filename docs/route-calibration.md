# Native route calibration

The native tools work again. The current HIDObservation build has effective Input Monitoring access. The updated NativeProbe has effective Accessibility, event-posting, and Screen Recording access. The user approved these grants. Refreshing the ad hoc app registrations made the grants effective.

## Console metadata does not establish route availability

The console registry still reported a lock while native Settings automation and capture worked. The earlier hard preflight treated that flag as a complete veto. That rule was too broad for this setup.

The runners now save console metadata as advisory context. A completed attack still counts as a bypass. A failed adapter remains inconclusive. The native action runner requires an explicit defensive refusal and a matched completed control before it reports a block. Ten Python tests cover the fixture, verifier, console observations, and action scoring.

This correction does not establish that the desktop was unlocked. It establishes that the tested operations worked despite the recorded flag. The earlier failed captures remain failed controls, with no prevention claim.

## Matched pixel capture pilots

The runner used fresh fixture content and the same HTML producer in each build. The only capture-policy difference was `AVSampleBufferDisplayLayer.preventsCapture`.

| Capture route | Control marker recovered | Protected marker recovered |
| --- | --- | --- |
| ScreenCaptureKit window | Yes | No |
| ScreenCaptureKit filtered display | Yes | No |
| System window screenshot | Yes | No |

Each row represents one trial per build with the original BGRA format. BGRA stores blue, green, red, and alpha values. A second pilot used NV12, a video format with separate brightness and color planes. It produced the same capture outcomes. The filtered display includes only the research window. It excludes other apps, the desktop, and the dock. The AX traversal recovered no marker from either renderer. These apps expose no input bridge.

Visual inspection showed a readable control page and a black protected page area in the saved screenshots. Both renderers submitted a frame and reported rendering status. That combination justifies further tests. It does not prove that the person sees the protected page on the physical display.

The user then reported a black protected BGRA page on the direct Mac display. The matched unprotected page was visible. This rejects the current BGRA configuration as useful capture protection. Black physical output cannot satisfy the browser goal.

The NV12 layers reported ready=true and obscured=false. The user also reported black physical NV12 output. This rejects the protected NV12 configuration as useful output on this machine. These diagnostics do not prove physical scanout. The [visibility research](research/capture-visibility.md) explains their documented meaning and the format comparison.

The [BGRA results](evidence/pixel-route-pilot.json) and [NV12 results](evidence/nv12-route-pilot.json) record captures and binary hashes. The [control capture](evidence/pixel-control-pilot.png) and [protected capture](evidence/pixel-protected-pilot.png) contain only disposable fixture content. The [operator observations](evidence/render-visibility.json) remain separate from automated capture scores. The [pixel implementation](pixel-rendering-findings.md) describes the producer and its limits.

## Next checks

Both protected windows failed the direct-display check. Other research-browser windows were closed at the user's request. The failed renderer candidates remain separate from native input experiments.

The next experiments test native input variants. Device observations require separate physical and synthetic sessions. Tool input cannot supply a physical baseline.
