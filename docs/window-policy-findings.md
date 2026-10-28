# Fixed window geometry experiment

Milestone 95 adds a diagnostic frame policy. Actual AppKit controls pass, but its external attack comparison remains inconclusive. No production browser policy changes.

The window captures its initial frame and refuses later changes through frame setters, zoom, and fullscreen. It also disables dragging and fixes its minimum and maximum size. This removes normal window movement and resizing for people too. It is an experimental compatibility tradeoff, not a distinction between human and agent input.

The platform control first confirms that ordinary move and resize operations work. It then pins that same window. Eight operations preserve its frame: direct and animated frame setters, origin and top-left setters, content resizing, zoom, simulated zoom, and fullscreen. These are calls within the test process. They do not prove resistance to external WindowServer operations. The test displays no window and sends no global input.

A separate readable shell compares ordinary and fixed modes. Both retain normal accessibility and system WebKit. It requests no permission, starts no input hook, and changes none of the frozen signed apps. Its optional launch flag exists only in this diagnostic. The controller arms one disposable task, checks a stationary baseline, and records an external zoom receipt. A successful reference is required before the fixed-mode comparison.

The first external pilot completes the ordinary startup task. Computer use then takes 137.8 seconds to return. This exceeds the controller's deadline, and the tool returns an empty window that it reopened after cleanup. No external zoom action occurs. The controller records the reference as inconclusive and skips the fixed mode. The reopened empty window is closed after exact executable verification. No block follows from this result.

All 139 Python checks pass. The AppKit controls pass. Secure Event Input is off, temporary policy processes are absent, and the five frozen browser/probe hashes match. See [receipts](evidence/window-policy-results.json).

Apple documents separate frame setters, zoom actions, and fullscreen actions. Its resize delegate does not cover every frame setter. The diagnostic therefore checks the window methods themselves. [NSWindow](https://developer.apple.com/documentation/appkit/nswindow), [window delegate](https://developer.apple.com/documentation/appkit/nswindowdelegate).

The next external experiment needs a working bounded driver. Do not integrate the policy as a proved defense before that comparison succeeds. Signal denial remains a separate problem. The [feasibility review](research/agent-free-feasibility-boundary.md) explains the missing entitlement, the untested identity-isolation option, and why changing one JavaScript clock cannot establish arbitrary-page resistance.
