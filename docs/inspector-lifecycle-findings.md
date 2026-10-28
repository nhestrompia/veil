# Inspector lifecycle and capture control

Milestone 147 finds an early failure in the external inspector client. The final trace sees a connected local target at startup, then no target about 55 milliseconds into its discovery loop. The helper's own logs record connection interruption, webinspectord validation failure, and invalidation. No reference page appears. This does not establish a browser defense or an entitlement requirement.

## Lifecycle controls

AppKit initialization with prohibited activation produces no discovery improvement. A queued main-thread callback runs, so the tested loop does process that callback. The client still sees no applications or pages. It sends no debugger message and opens no channel.

The own-client logs show two internal target connections with explicit initialization. An experiment leaves creation entirely to the framework. It sees no usable current-machine target. Its own logs still record one connection and the same validation failure. Thus removing explicit creation does not resolve the failure. The final diagnostic retains explicit initialization. The two internal targets are not established as a framework bug.

Earlier reports record whether a connection was ever present. They do not prove continuous connectivity. The milestone 146 wording that described connectivity throughout the trial is withdrawn. The diagnostic now records target disappearance and the final target state. In the final control, the target is absent at the end and needs no removal request.

## Scoped log collection

The new collector filters the exact helper PID and executable path. It reads only that process's XPC and WebInspector events. It does not read daemon or unrelated-process logs. It saves fixed event categories and connection aliases. Raw messages, device names, object addresses, and private payloads do not enter its output.

Four tests cover private-payload removal, unrelated endpoints, malformed records, exact process filtering, and failed log commands. Seventeen relevant Python checks pass. Seven native boundary controls refuse before client initialization. Swift 6 compilation with warnings as errors and Python compilation pass.

## Capture and remaining limits

A fresh fullscreen readable reference fails the unchanged recorder's coverage guard. Another window intersects the crop. This check captures no pixels. It does not identify which window caused the current overlap. The earlier rejected notification inspection remains outside this trial. No attempt reads that notification or bypasses the guard.

All five inspector references and the capture reference close. Their fixtures stop, with no task submissions. No client or recorder process remains. The preview and granted recorder preserve their hashes. No grant request, administrator access, physical input, or browser rebuild occurs.

The next inspector step must resolve the client-side validation failure and recover a readable reference before a protected comparison. Its exact cause remains unknown. Capture still needs valid owned coverage, followed by a fresh physical candidate control. Agent-free acceptance remains unmet.

See [saved results](evidence/inspector-lifecycle-results.json) and [earlier connection findings](inspector-connection-findings.md).
