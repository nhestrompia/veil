# Local developer tools at launch

The installed WebKit framework accepts `-WebKitDebugDeveloperExtrasEnabled YES`. The diagnostic preference getter returns true while `WKWebView.isInspectable` remains false. Three fresh launches repeat this result. Three explicit-NO controls return false.

This confirms a launch setting for local developer tools. It does not establish external inspector attachment or a completed website action. The private getter exists only in the separate diagnostic app.

## Startup rule

The browser now sets that key to false in its process-local argument domain before it creates AppKit or WebKit objects. It preserves other argument values. If the effective setting remains true, startup stops. The inspectable reference build retains its existing behavior.

Three fresh diagnostic launches with the YES argument and the same startup rule return false for both the effective default and developer extras. Every launch preserves a separate sentinel argument. All nine preference checks pass. The policy uses public Foundation APIs and writes no persistent preferences.

Apple documents the argument domain as volatile and gives it precedence over ordinary saved app settings. This explains why a normal persistent preference write would not address this launch argument. Managed policy and future framework changes require separate checks. [Apple defaults guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/UserDefaults/AboutPreferenceDomains/AboutPreferenceDomains.html)

The [source investigation](research/inspector-launch-boundary.md) identifies the setting and the separation between local inspection and remote inspectability. Its upstream findings remain separate from these installed-framework measurements.

## Evidence and limits

The [nine-run results](evidence/inspector-launch-results.json) include process IDs, system version, and the diagnostic binary hash. A revised internal browser control preserves the startup address, opens the address editor through Command-L, and completes one independent fixture action. That sequence uses private diagnostic events. It does not supply physical input or an external bypass.

The production keyboard browser compiles with Swift 6 warnings as errors. Twelve address-policy cases and fifteen Python checks pass. The fixture check requires loopback socket access.

No new human usability result exists for this binary. No successful inspector attachment exists in this milestone. WebAssembly debugging, drag delivery, other semantic actions, and device-origin attacks still need controls. The agent-free requirement remains unmet.

```sh
bash scripts/build-inspector-control.sh
python3 tools/run_inspector_launch.py
bash scripts/build.sh devicekeyboard
bash scripts/diagnose-browser-keyboard.sh --capture-restricted --build-only
python3 tools/run_internal_keyboard_control.py --output artifacts/inspector-policy-browser-control
```
