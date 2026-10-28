# Inspector connection diagnosis

Milestone 146 observes a local target that reports connected and ready. Explicit listing and identifier requests still return no applications or fixture pages. These client-side flags do not prove a daemon acknowledgment. No debugger channel opens, no script runs, and no protected candidate launches.

## Four readable controls

The first control adds connection-state observations to the existing discovery loop. Its local target initially reports a connection object, connected true, and ready true. Milestone 147 corrects the earlier claim of continuous connectivity. It records target disappearance during the trial. NSApp is absent. These observations reject a missing connection object as the immediate explanation. They do not establish client admission or a complete protocol handshake.

The next control attempts an explicit application-listing request. The method check refuses before invocation. Runtime metadata shows that RWIManager does not implement the requested RWIBaseManager method. The corrected control obtains the manager's message receiver and checks that object's method encoding. Its listing call runs, but the application count remains zero.

The final control adds the observed identifier request before the listing request. Both requests run against the same local target. The application count remains zero, with no owned application or matching page. The client requests removal of its local target and confirms its absence afterward.

The native helper reads only aggregate application counts and exact owned-process matches. It saves no unrelated page URLs or titles. Existing host, renderer, fixture, duration, and no-script boundaries remain. Method errors now identify the fixed selector name that failed, without saving external payloads.

## Result integrity fix

The Python runner previously promoted discovery before it checked the independent oracle and resource cleanup. Thus an unexpected task action or failed cleanup could leave a saved success label. Two regression tests reproduce that defect before the fix.

The runner now promotes a reference only after the oracle reports no task action and both resources close. All three new regression tests pass, including the clean-success control. Thirteen relevant Python checks pass. Five native boundary controls refuse before client initialization. Swift 6 compilation with warnings as errors and Python compilation pass.

## Limits and next step

All four references and fixtures close, with zero oracle submissions. No client process remains. The preview and granted recorder retain their pinned hashes. No permission request, administrator action, physical input, screen capture, or browser rebuild occurs.

Console observation returns no lock flag. It does not establish a locked or unlocked session. Do not request an unlock based on that result. Application lifecycle, client admission, and remaining discovery requirements are still unknown. No signing or entitlement requirement follows from these trials.

The current client command supports a passive control, --fetch-listing, or --register-and-list. The two request modes are mutually exclusive. None is a calibrated attachment test. Require successful reference discovery and an actual script read or task action before any protected-browser comparison.

See [results](evidence/inspector-connection-results.json), [earlier controls](inspector-discovery-control-findings.md), and [client research](research/cocoa-inspector-client.md). Agent-free acceptance remains unmet.
