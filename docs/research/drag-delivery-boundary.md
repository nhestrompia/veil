# External drag delivery boundary

Research date: 2026-10-23. Scope: the keyboard-only macOS WKWebView host. This note describes public AppKit APIs and current upstream WebKit source. The installed framework can differ from upstream. No app, drag, permission request, or preference change ran for this investigation.

A drag session needs its own refusal path. The strongest public candidate is a WKWebView subclass that refuses the destination callbacks before calling WebKit. An `NSApplication.sendEvent` gate alone does not establish this boundary.

## Drag sessions have separate destination callbacks

AppKit starts a session through `NSView.beginDraggingSession(with:event:source:)`. The supplied event supplies the initial mouse location. AppKit then manages a session with dragging items and a source object. Apple documents the actual start on the next run-loop turn. The source API does not document physical-input authentication. [Drag source API](https://developer.apple.com/documentation/appkit/nsview/begindraggingsession(with:event:source:)), [NSDraggingSession](https://developer.apple.com/documentation/appkit/nsdraggingsession)

A destination receives `NSDraggingInfo` through `draggingEntered`, `draggingUpdated`, `prepareForDragOperation`, and `performDragOperation`. These methods differ from ordinary mouse responder methods. Apple documents `.none` as a refusal during entry or update. Returning `.none` on entry does not prevent later update or exit callbacks. `performDragOperation` imports the data after preparation succeeds. [draggingEntered](https://developer.apple.com/documentation/appkit/nsdraggingdestination/draggingentered(_:)), [performDragOperation](https://developer.apple.com/documentation/appkit/nsdraggingdestination/performdragoperation(_:))

The current application gate checks individual `NSEvent` objects in `sendEvent`. The reviewed WebKit drag callbacks call the drag implementation directly. That implementation does not call the host's `sendEvent`. This creates a specific hypothesis that destination callbacks can reach the page without an authorized keyboard event. It does not prove that the external source can complete a session on this Mac. AppKit's complete internal delivery mechanism is not established here. [DeviceKeyboard.swift](../../Sources/Browser/DeviceKeyboard.swift), [WKWebViewMac.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm)

## macOS receives the main page drag on WKWebView

Current `WKWebViewMac.mm` implements the public destination methods on `WKWebView` itself. They call `WebViewImpl::draggingEntered`, `draggingUpdated`, `prepareForDragOperation`, and `performDragOperation`. The macOS path does not require an iOS `WKContentView` override. An ordinary WKWebView subclass therefore has a concrete interception point for this main-page path. [WKWebViewMac.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm)

`WebViewImpl` registers editing, URL, and dummy pasteboard types on its view during initialization. Entry and update construct `DragData` and call the page proxy. `prepareForDragOperation` currently returns true. Drop handling calls `WebPageProxy::performDragOperation`, with separate handling for files and file promises. [WebViewImpl.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm)

WebCore can dispatch a DOM drop, edit content, or load a URL. Entry and update can also reach document drag handling. Thus a refusal only at `performDragOperation` leaves earlier page callbacks available. A navigation policy cannot cover all document editing and DOM drag handlers. [DragController.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/DragController.cpp)

This source path does not establish every installed native child view's behavior. A subclass override on the outer view does not automatically override another object's methods. Native controls, field editors, document viewers, and extra windows need separate coverage if the host permits them.

## Public refusal methods and their limits

For a host that intentionally supports keyboard input only, these are the smallest explicit public refusals on the owned WKWebView:

| Method | Refusal |
| --- | --- |
| `draggingEntered(_:)` | Return `[]`, without `super` |
| `draggingUpdated(_:)` | Return `[]`, without `super` |
| `prepareForDragOperation(_:)` | Return `false`, without `super` |
| `performDragOperation(_:)` | Return `false`, without `super` |

`[]` is the empty Swift `NSDragOperation` mask, equivalent to `NSDragOperationNone`. The installed macOS 27.0 SDK declares `NSView` as an `NSDraggingDestination`. Apple documents entry refusal and the preparation condition for data import. Refusal before the superclass call also avoids WebKit's page notification on the reviewed path. [Apple destination contract](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/DragandDrop/Tasks/acceptingdrags.html), [WebKit destination forwarding](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm)

`unregisterDraggedTypes()` unregisters the receiving view. It does not describe a recursive policy for its descendants or the window. Moreover, WebKit implements a separate private `_hitTest:dragTypes:` path that returns its view even when types do not match. Thus unregistering types is useful supporting work, but source review does not establish it as a complete WKWebView defense. The public callback refusals avoid dependence on that private selector. [Apple drag APIs](https://developer.apple.com/documentation/appkit/nsview/begindraggingsession(with:event:source:)), [WebKit drag hit testing](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm)

Apple describes public `NSView.hitTest(_:)` primarily as mouse-down routing. WebKit's separate drag hit-testing method prevents treating a content-view override as proof that every drag follows ordinary hit testing. A rejecting container or overlay needs a live callback test. It cannot replace a destination refusal based on this evidence. [Apple hitTest contract](https://developer.apple.com/documentation/appkit/nsview/hittest(_:)), [WebKit drag hit testing](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm)

The host can apply the same public refusal policy to its owned window and editable controls. `NSWindow` also exposes registration methods in the installed SDK. Unregistering the window alone does not unregister the WKWebView. Any temporary field editor needs attention because it is a separate destination object.

## WKUIDelegate does not supply a public general veto

Neither current upstream `WKUIDelegate.h` nor the installed public header declares a general drag-destination decision method. The destination-action mask method is `_webView:dragDestinationActionMaskForDraggingInfo:` in `WKUIDelegatePrivate.h`. The similarly named `WebUIDelegate` belongs to legacy `WebView`. Neither is a public WKUIDelegate solution for this host. [Public WKUIDelegate](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKUIDelegate.h), [private WKUIDelegate](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKUIDelegatePrivate.h), [legacy WebUIDelegate](https://developer.apple.com/documentation/webkit/webuidelegate)

Current macOS WebKit also excludes drop-to-navigate from its default action mask for newer SDK-linked hosts. A failed URL drop can therefore reflect baseline policy. It cannot establish the keyboard gate's effect. Text insertion or a fixture DOM drop handler supplies a better positive control. [Default destination-action mask](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm)

## Runtime evidence remains absent

The parent reports a locked session and `cgWindowNotFound` during native UI access. No valid external drag run exists. The fixed-payload DragSource and the research-drag probe route do not themselves establish delivery, a bypass, or a block.

The next live experiment needs a usable session and matching controls:

1. Complete a fixed-text external drop into the control fixture. Record the source session start, destination callbacks, and a server-observed fixture result.
2. Repeat against the current keyboard-only host. Record page drag events separately from its `sendEvent` refusal counters.
3. Repeat after public destination refusals. Establish that the same source still works on the control. Require no page entry, update, or drop events on the protected fixture.

A failed source session or missing target window makes the attempt inconclusive. Zero completed drops alone cannot prove that the browser rejected external drag delivery.
