# Browser navigation controls

Milestone 109 adds Forward, state-based Back and Forward controls, and Reload/Stop behavior. The address updates when a document commits. The window subtitle shows page loading, stopped loads, and network errors. The protection footer keeps its separate status. Command-L selects the address in the ordinary shell. The device experiment retains its physical keyboard route.

A separate sandboxed diagnostic builds from the same browser controller. It uses a hidden window and a disposable loopback fixture. Ten checks pass through the actual address and button actions. They cover empty history, first-page history, Back, Forward, Reload, loading feedback, Stop, network errors, recovery, and hidden-window behavior. Server receipts confirm requests to both pages, the slow response, and the failed response. The host and all three measured WebKit processes exit.

The first control fails after the loading-feedback check. It stops a provisional load before the server receives the slow request. The revised control waits for the slow document title before Stop. It then passes every check. The saved evidence retains both results. This repair changes the test timing, not the browser behavior.

The browser policy checks pass. Device keyboard source passes Swift 6 type checking with warnings as errors. The separate diagnostic builds with the same compiler checks. All five frozen executable hashes match. The active comparison command, four staged images, eight ordinary source files, and signal actor also match their approved hashes.

This is an owner-driven functional check. It does not test external agents or physical human input. It does not close the known renderer pause bypass. The frozen permissioned browser does not contain these source changes. General website compatibility, pointer input, isolated-controller integration, and agent-free acceptance remain open.

The approved comparison set is separate milestone 108 work. Its first invocation currently waits for macOS authentication before staging. No signal-denial result exists for that set yet. Root scope and the three-attempt limit remain unchanged.

See [saved evidence](evidence/browser-navigation-results.json).

To reproduce, run `bash scripts/build-browser-navigation-control.sh`. Then run `python3 tools/run_browser_navigation_control.py --out artifacts/browser-navigation-new`. Use a new output directory. The diagnostic requests no privacy grant and installs no input hook. App Sandbox can create its own application container.
