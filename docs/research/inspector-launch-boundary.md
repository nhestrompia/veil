# Inspector launch boundary

Research date: 2026-10-23. Scope: an intact macOS Cocoa host with `WKWebView.isInspectable = false`. This review used current upstream source and existing project evidence. It did not launch apps, change preferences, request grants, or attach an inspector. Upstream `main` does not establish the behavior of the installed system framework.

The clearest launch argument enables local developer tools. It does not prove that an agent can open those tools through the current input gate. A separate WebAssembly debugger has a concrete environment switch, but its availability in this host remains unknown.

## Local developer tools can read launch arguments

`WKPreferences.init` constructs `WebPreferences` with an empty identifier, `WebKit` as its key prefix, and `WebKitDebug` as its debug prefix. The exact candidate is `-WebKitDebugDeveloperExtrasEnabled YES`. The often suggested `WebKit2DeveloperExtrasEnabled` key does not follow this constructor. [WKPreferences.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKPreferences.mm)

`DeveloperExtrasEnabled` defaults to false and declares `defaultsOverridable: true`. The preference file documents the `WebKitDebug` prefix for these overrides. [UnifiedWebPreferences.yaml](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml)

Cocoa preference initialization reads these debug keys through `NSUserDefaults.standardUserDefaults`. It does this before returning for an empty identifier. Thus an empty identifier does not prevent this specific debug override. The same lookup can read an existing app preference. This research did not write one. [WebPreferencesCocoa.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Cocoa/WebPreferencesCocoa.mm)

Apple documents command-line defaults as volatile overrides. `NSArgumentDomain` precedes the app's persistent defaults. A direct executable launch with the argument can therefore test this route without a persistent preference change. [Apple user defaults guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/UserDefaults/AboutPreferenceDomains/AboutPreferenceDomains.html)

WebCore adds **Inspect Element** to the context menu when developer extras are enabled. Selecting that item calls the page's inspector controller. This gives a concrete local entry point without Safari settings. [ContextMenuController.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/ContextMenuController.cpp)

The local inspector's `connect()` and `openLocalInspectorFrontend()` check `developerExtrasEnabled()`. Neither reviewed function checks `inspectable()`. The `WKWebView` inspectability setter also retains a FIXME about local inspection. WebKit tracks that separation in an open bug. These source facts justify a local-inspector experiment. They do not establish a bypass of the input gate. [WebInspectorUIProxy.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Inspector/WebInspectorUIProxy.cpp), [WKWebView.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKWebView.mm), [WebKit bug 246237](https://bugs.webkit.org/show_bug.cgi?id=246237)

No automatic-open default emerged from the reviewed initialization and inspector code. `InspectorStartsAttached` selects attachment after the inspector opens. It defaults to true and lacks `defaultsOverridable`. `WebInspectorEngineeringSettingsAllowed` permits an inspector feature, but the reviewed code gives it no automatic-open role. This is a bounded source result, not an exhaustive absence proof. [Inspector preferences](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml), [local inspector connection](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Inspector/WebInspectorUIProxy.cpp)

## Cocoa remote inspection has a separate policy

WebKit documents `isInspectable` as a per-view opt-in. Its default is false. Current Cocoa source derives legacy defaults from SDK behavior and signed entitlements. `JSRemoteInspectorSetInspectionEnabledByDefault` changes process state through a function call. It is not an external launch switch. Calling it inside another process would require a route outside this investigation. [WebKit inspectability API](https://webkit.org/blog/13936/enabling-the-inspection-of-web-content-in-apps/), [JSRemoteInspector.cpp](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/API/JSRemoteInspector.cpp)

The Cocoa relay omits a target from its listing when `allowsInspectionByPolicy()` is false. Connection setup separately checks `remoteControlAllowed()`. Guessing a target identifier does not remove that second check in the reviewed code. Starting the relay and permitting a specific page are separate operations. [RemoteInspectorCocoa.mm](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm), [RemoteConnectionToTargetCocoa.mm](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteConnectionToTargetCocoa.mm)

There are explicit exceptions. `remoteControlAllowed()` also accepts a target with a local debugger. Cocoa policy can permit an otherwise non-inspectable target on an internal security-policy variant. That path calls `os_variant_allows_internal_security_policies("com.apple.WebInspector")`. No ordinary argument-domain default that activates this OS policy emerged from this review. No internal-policy or notification state changed. [RemoteInspectionTarget.cpp](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/RemoteInspectionTarget.cpp)

## Environment switches need port and process checks

`WEBKIT_INSPECTOR_SERVER` and `WEBKIT_INSPECTOR_HTTP_SERVER` are documented for WebKitGTK and WPE. Their documented TCP servers do not establish a Cocoa server. Cocoa uses a different relay implementation. [WebKit environment-variable reference](https://trac.webkit.org/wiki/EnvironmentVariables), [Cocoa remote inspector](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm)

Cocoa JavaScriptCore does parse `JSC_` environment options. Its client customization runs after this parsing. `OptionsList.h` declares `enableWasmDebugger` as a normal option. Thus `JSC_enableWasmDebugger=true` is a concrete engine option, unlike a guessed page-inspection switch. [Options.cpp](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/runtime/Options.cpp), [OptionsList.h](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/runtime/OptionsList.h)

Current upstream enables WebAssembly debugger support by default on macOS with WebAssembly. The WebContent startup path also requires ARM64. When its option is true, that process starts Remote Web Inspector communication and sends `WasmDebugServerReady`. The UI process then creates a separate target with `setInspectable(true)`. [PlatformEnable.h](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/PlatformEnable.h), [WebProcess.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/WebProcess/WebProcess.cpp), [WebProcessProxy.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/WebProcessProxy.cpp)

This is not a demonstrated page-inspector override. Page creation normally forwards `WebAssemblyDebuggerEnabled` as a process parameter. That preference lacks `defaultsOverridable`. The reviewed Cocoa launcher does not explicitly forward `JSC_` variables. Whether the installed XPC service receives a variable from this host remains unknown. An app launch alone cannot establish propagation. [WebProcessPool.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/WebProcessPool.cpp), [preference declaration](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml), [ProcessLauncherCocoa.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Launcher/cocoa/ProcessLauncherCocoa.mm)

The debugger exposes WebAssembly state through a process-wide target. Its documented external relay uses `WebInspector.framework`. The standalone TCP mode belongs to the JavaScriptCore shell. Neither mode proves arbitrary DOM access, page navigation, or successful attachment to this browser. [WebAssembly debugger architecture](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/wasm/debugger/RWI_ARCHITECTURE.md)

Playwright's own WebKit patch adds protocol domains, including `Playwright` and `Input`. Success with that binary is not a positive control for attachment to an intact Cocoa host. [Playwright's WebKit patch](https://github.com/microsoft/playwright/blob/main/browser_patches/webkit/patches/bootstrap.diff)

## Existing evidence and bounded next attacks

The saved [discovery evidence](../evidence/inspector-discovery.json) records an inspectable control in Safari Develop and no protected target. Attachment remained inconclusive because of an Accessibility error. This establishes discovery behavior only. This investigation added no runtime evidence.

The next experiments can stay within the existing research app and loopback fixture:

1. Launch separate baseline and protected instances with `-WebKitDebugDeveloperExtrasEnabled YES`. Attempt the page context menu through already permitted synthetic input. Record an inspector window separately from successful fixture access. A refused pointer event cannot prove that the preference failed.
2. If the local inspector opens, attempt one fixture read and one fixture action through its console. The target's application input gate also applies to the new inspector window. Human assistance would measure exposure after a human action, not an autonomous agent bypass.
3. Evaluate `JSC_enableWasmDebugger=true` only with a working client that restricts discovery to this research app. Establish WebContent propagation and the separate target before sending any debugger command. Do not alter launchd state, Safari settings, or other apps.

No working local-inspector control exists in the saved evidence. No working WebAssembly relay control exists here either. Without those controls, failed attachment remains inconclusive. No reviewed launch default automatically opens the local inspector or replaces the ordinary page's remote policy. The available evidence therefore does not establish a complete bypass or prove that all launch routes fail.
