# Protected pixels with device-source keyboard routing

Milestone 121, October 27, 2026. A separate browser combines the compressed protected-pixel producer with the earlier device-source keyboard policy. The reproduced launch-only action stops in this image. A process-local routing control completes one form action. Physical use of this new app remains unverified because its Input Monitoring grant is absent.

## Demonstrated bypass and defense

The original protected-pixel app immediately loads an agent-supplied `--url`. A local page records a harmless action on load. The [external audit](pixel-agent-audit-findings.md) reproduces that action without screenshots or input.

`PixelKeyboardExperiment` only prefills the supplied address. It does not call `load` at startup. The existing keyboard router must bind a permitted built-in device while this window has focus. The address editor then requires Return before navigation. External URL-open events refuse. App-level injected input does not enter the router's authorized-event set.

The new window keeps the WebView and address editor outside its clipped visible bounds. They remain native keyboard responders in the same window. Only the compressed page image and drawn address reach the visible media layer. The address is therefore part of the protected producer rather than a separate clear address bar. Live capture of the new combined app remains unverified.

The app disables inspection and developer extras, uses ephemeral website data, rejects downloads and new windows, and reuses the existing content/export restrictions. Mouse input remains disabled. Text routing supports the existing US ASCII map. This is a keyboard-only research browser.

## Calibration and repeat attacks

The unprotected `PixelKeyboardRoutingControl` contains a compile-time event generator. It internally authorizes process-local events, opens the address, Tabs to the form, types the fixed fake phrase, and submits it. The oracle accepts exactly one action. The capture shows the completed page and its address. This proves routing and rendering, not physical human input or resistance to an outside agent.

The generator is absent from the protected image. Static strings confirm that distinction. The final Return-only delegate also avoids duplicate navigation from ordinary field-edit completion. One authorized Return now produces one navigation in the control.

The final launch comparison records a page-ready event and accepted action in the old protected app. The new app records neither. Its log retains `pendingPhysicalSubmit=true` and no permission request. This is the measured startup defense. Human usability and post-enrollment attacks still need a physical baseline.

A real Playwright/CDP client attaches to an isolated Chrome profile, reads its marker, and completes its form. The same client receives connection refusal from both native pixel apps at the requested debugging ports. This tests the specified CDP launch-flag route. It does not prove that every WebKit inspector transport refuses attachment.

The final combined app also refuses an external URL-open event. Host AX traversal returns only its application root. Direct system AX queries fail their foreground check, and window capture returns ScreenCaptureKit error -3811. Those two failures remain inconclusive. No screenshot-prevention claim follows from that run.

## Permissions and desktop safety

The user then authorized this grant in Settings. The readable pane listed DeviceKeyboardExperiment and HIDObservation, but omitted PixelKeyboardExperiment. The Add click returned `windowNotFoundAtPosition`. Settings then appeared dimmed. The tool did not show an authentication prompt. A system-dialog observation stalled for 1261 seconds despite its 20-second timeout. The unchanged app still reports `listenGranted=false`. Neither the grant nor the app addition has confirmation. Native UI control cannot complete this step.

The user approved the exact PixelKeyboardExperiment Input Monitoring request. The request ran through LaunchServices and exited zero. The unchanged binary still reports `listenGranted=false` after the request and on a later read. The earlier automatic approval rejection is resolved by this consent.

System Settings returns `cgWindowNotFound` on two UI attempts. Opening the Input Monitoring pane succeeds, but the UI tool cannot read its window. No switch, reset, re-add, authentication, or other grant change occurs. The user must enable this app in that pane before physical tests can proceed. Do not claim that the Mac is locked from this error.

Keep the manifest-pinned app unchanged. The next tests require physical navigation and form completion, then external attacks against the same loaded session. No physical baseline or new attack result follows from the permission request.

The new app reports `listenGranted=false`. The original DeviceKeyboardExperiment grant belongs to a different app identity. The new app never automatically requests a grant. Its explicit request mode is ready, and the [permission manifest](evidence/pixel-keyboard-permission-manifest.json) pins both binaries.

Input Monitoring permits system-wide keyboard observation. The reused router processes input only while this research window has focus and saves no typed text or key codes. It installs no event tap and opens devices without seizure. The app is unsandboxed, matching the earlier device-routing experiment.

Existing modifying mouse hooks remain active. No external synthetic input runs, and no unrelated process stops. All five frozen permissioned executables retain their hashes. Strict signatures and Swift 6 warnings-as-errors builds pass. The original H.264 branch typechecks. Python, JavaScript, and shell syntax checks pass.

## Next valid checks

After an approved grant, keep this exact image unchanged. Obtain a physical navigation and form-completion baseline. Then repeat the external AX, capture, blind-input, and keyboard attacks against that same live session. Synthetic-input tests also need the desktop safety guard to pass.

Unfiltered display capture, continuous recording, direct renderer AX, lifecycle/timing actions, and broader page compatibility remain open. The older signal-isolation experiment is not integrated into this app. No agent-free result follows from this milestone.

```sh
bash scripts/build-pixel-keyboard.sh
python3 tools/run_pixel_keyboard_calibration.py --output artifacts/pixel-keyboard-routing-repeat
python3 tools/run_pixel_agent_audit.py --launch-only --launch-targets PixelH264ProtectedExperiment PixelKeyboardExperiment --output artifacts/pixel-keyboard-launch-repeat
```

See [saved results](evidence/pixel-keyboard-results.json) and [the route inventory](agent-attack-inventory.md).
