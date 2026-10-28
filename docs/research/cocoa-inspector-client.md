# Cocoa inspector client feasibility

Research date: 2026-10-28. This note reviews upstream `main`, not the installed framework's implementation. No app, UI, permission, or live relay action ran during this research.

An external Cocoa client still needs a discovery and transport implementation. The reviewed WebKit frontend SPI does not supply one. Existing Safari success establishes an inspectable reference control. The protected target's omission remains a discovery result, as recorded in [the project findings](../safari-remote-findings.md).

## Frontend and metadata

The public `WKWebView.isInspectable` API controls whether a view permits inspection. WebKit documents Safari's Develop menu as its client workflow. This documentation does not specify a public Cocoa client API for an unrelated process. [WebKit API announcement](https://webkit.org/blog/13936/enabling-the-inspection-of-web-content-in-apps/)

`_WKRemoteWebInspectorViewController` exposes a frontend window and web view. Its caller supplies debuggable metadata and a backend-commands URL. Backend messages leave through `inspectorViewController:sendMessageToBackend:`. Replies enter through `sendMessageToFrontend:`. The associated proxy creates the frontend page and forwards backend messages to its client. These interfaces require the caller to supply the connection. [Controller header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/_WKRemoteWebInspectorViewController.h), [proxy implementation](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Inspector/RemoteWebInspectorUIProxy.cpp)

`_WKInspectorDebuggableInfo` explicitly describes itself as transient and data-only. It does not uniquely identify a target across calls. Its fields describe target type, platform, versions, and simulator status. Constructing it cannot select a process or establish a relay channel. [Metadata header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/_WKInspectorDebuggableInfo.h)

## Cocoa transport and authorization limits

On macOS, `RemoteInspectorCocoa` creates an XPC connection to the inspector Mach service. `RemoteInspectorXPCConnection::handleEvent` checks the connection peer's audit token for `com.apple.private.webinspector.webinspectord`. This authenticates the relay peer seen by the target-side connection. It does not prove that an external debugger must possess that entitlement. These files do not establish the daemon's separate client-admission rules. [Cocoa connection](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm), [peer validation](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteInspectorXPCConnection.mm)

WebKit's architecture document places the external Wasm relay in a separate repository. It uses `WebInspector.framework` for discovery and connection management through `webinspectord`. It forwards GDB packets, while ordinary page inspection uses JSON messages. The document supplies no external client implementation or signing requirements. [Architecture](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/wasm/debugger/RWI_ARCHITECTURE.md)

The parent investigation reports installed private-framework classes `RWIManager`, `RWIDebuggable`, and `RWIChannel`. Reported selectors include `openChannelForDebuggable:error:`, `start`, and `sendMessageToBackend:`. This local metadata identifies possible client entry points only. It establishes neither authorization nor attachment success. Missing public symbols or headers also do not establish security enforcement.

## Other ports and protocols

GLib uses socket connections and typed messages such as `GetTargetList`, `Setup`, and `SendMessageToTarget`. That implementation does not establish a compatible Cocoa endpoint. [GLib implementation](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/glib/RemoteInspectorGlib.cpp)

Playwright's `connectOverCDP` supports Chromium browsers only. Its WebKit patch adds domains including `Input` and `Playwright`. Neither API establishes attachment to an intact Cocoa host. [Playwright API](https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp), [WebKit patch](https://github.com/microsoft/playwright/blob/main/browser_patches/webkit/patches/bootstrap.diff)

## Next scoped experiment and unknowns

Prepare an offline client adapter around the installed `RWIManager` and `RWIChannel` declarations. Compile it with mocked discovery and message callbacks. Test exact research-process selection, rejection of unrelated targets, bounded logs, and channel cleanup. Do not instantiate the manager or contact the relay in this step. A later live experiment needs an inspectable disposable reference before any protected-target comparison.

Unknowns remain the installed daemon's client-admission policy, required signing or entitlements, private API compatibility, and target-policy refusal behavior. The Wasm README now names `__XPC_JSC_enableWasmDebugger=1 JSC_enableWasmDebugger=1`. Treat this as a separate future propagation experiment after the client works. It proves no installed behavior or DOM access. [Current README](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/wasm/debugger/README.md)

## Installed metadata control

The new InspectorRelayMetadata diagnostic loads only the fixed system WebInspector framework. It reads runtime metadata for ten named classes. It creates no client, invokes no client method, and requests no relay connection. It rejects root execution and extra arguments. A five-second alarm bounds execution. It requests no macOS grant and posts no input.

On macOS 26.6, all ten classes exist. RWIManager exposes openChannelForDebuggable:error:. RWIChannel exposes start, sendMessageToBackend:, and close. RWIServiceXPCConnection exposes initWithMachine:xpcServiceName:delegate:. The saved report includes their Objective-C type encodings. Compilation with Swift 6 warnings as errors passes. The live metadata command passes, and an extra-argument control exits with code two.

These results identify installed interfaces. They do not establish how to initialize a scoped client or whether the daemon accepts it. The diagnostic does not audit dynamic-library initializers or monitor relay traffic. No attachment, script read, or script action runs. No browser image or granted helper changes.

The source is Sources/Diagnostics/InspectorRelayMetadata.swift. The bounded [metadata results](../evidence/inspector-relay-metadata-results.json) preserve the installed evidence. Full local reports remain in artifacts/inspector-client-144. Agent-free acceptance remains unmet.

The later [discovery control](../inspector-discovery-control-findings.md) implements the installed lifecycle interfaces. Three readable references remain undiscovered. That result does not establish attachment refusal or daemon admission policy.
