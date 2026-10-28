# External inspection of the browser preview

Research date: 2026-10-28. No external attachment client was validated under the present constraints. Remote inspection remains untested on the frozen preview. This review changed no apps, settings, permissions, or browser code.

## What the policy covers

Apple documents `WKWebView.isInspectable` as the switch for Safari Web Inspector access. It defaults to false. Setting it to false during inspection closes the inspector and stops further content access. That is a documented API contract, not this project's live attachment result. [Apple API documentation](https://developer.apple.com/documentation/webkit/wkwebview/isinspectable)

The reviewed Cocoa source enforces the remote policy twice. `listingForInspectionTarget()` omits targets when `allowsInspectionByPolicy()` returns false. Connection setup also checks `remoteControlAllowed()` before it connects. Hiding a listing and refusing attachment are distinct operations. [Cocoa listing code](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm), [connection setup](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteConnectionToTargetCocoa.mm)

The source permits exceptions for an existing local debugger and an internal OS security policy. Ordinary public documentation does not make those exceptions an external override available to this test. Source on `main` also cannot establish the installed framework's behavior. [Remote inspection policy](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/RemoteInspectionTarget.cpp)

Local inspection needs its separate rule. `WebInspectorUIProxy::connect()` checks `developerExtrasEnabled()`. The saved [local test](../local-inspector-policy-findings.md) demonstrated a console read and action when the launch override enabled developer extras. The protected shell suppressed the tested menu route. These results concern a separate shell and one entry point, not the integrated preview. [Local inspector source](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Inspector/WebInspectorUIProxy.cpp)

## Client options

| Option | Concrete interface | Limit for this experiment |
| --- | --- | --- |
| Safari Web Inspector | Develop → this Mac → inspectable research view | Official client. WebKit requires the developer-features setting. This review did not change it. |
| Cocoa inspector frontend | `_WKRemoteWebInspectorViewController` | Exposes `loadForDebuggable:backendCommandsURL:` and a delegate for backend messages. It supplies the inspector frontend, not discovery or a backend connection. |
| Cocoa relay | `com.apple.webinspector` and `com.apple.webinspector.debugger` | Primary source names the Mach services. It does not supply a complete standalone debugger client or establish that this ordinary process can use one. |
| WebAssembly relay | `WasmDebuggerRWIClient` | Upstream describes a separate repository but supplies no client source location here. Its target and protocol concern WebAssembly, not ordinary page inspection. |
| Safari MCP/WebDriver | `/usr/bin/safaridriver --mcp` | Safari 27 documents agent access, with a Safari developer setting. It does not document attachment to an arbitrary WKWebView host. |

Sources for the table: [official Safari setup](https://webkit.org/web-inspector/enabling-web-inspector/), [frontend header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/_WKRemoteWebInspectorViewController.h), [relay constants](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/RemoteInspectorConstants.h), [WebAssembly architecture](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/wasm/debugger/RWI_ARCHITECTURE.md), [Safari 27 agent support](https://webkit.org/blog/18325/webkit-features-for-safari-27-0/), [Safari driver scope](https://developer.apple.com/documentation/webkit/testing-with-webdriver-in-safari).

## Next experiment

The next runnable step is a client preflight, not a preview attachment. A separate ordinary CLI can load the installed WebKit framework and inspect Objective-C class metadata without creating views. Check `_WKRemoteWebInspectorViewController` and the selectors listed above. Record class availability and method type encodings. Do not instantiate the controller, send relay messages, post input, or request permission. This checks the installed interface and leaves the frozen browser untouched.

A successful preflight still supplies no backend transport. Require a working, bounded discovery client before testing the candidate. Calibrate that client against one disposable inspectable control. Match ownership before any read and request only its random fixture marker. Then test the unchanged preview. A failed control makes the candidate result inconclusive.

No complete standalone Cocoa client emerged from the reviewed primary sources. Do not invent an attachment result from a port scan. Cocoa uses XPC, so no TCP listener does not prove that external inspection is blocked. [Cocoa transport source](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm)
