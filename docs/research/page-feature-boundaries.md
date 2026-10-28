# Native page features outside the input gate

Research date: October 25, 2026. No UI actions, permission changes, or app rebuilds formed part of this research.

The browser needs policy for native features that WebKit creates after a page request. Filtering `NSApplication.sendEvent` alone does not cover these callbacks. The source findings below identify test targets. They do not establish an external attack success.

## Scope and source limits

Local source reviewed: `BrowserApp.swift`, `BrowserPolicy.swift`, `AXBoundary.swift`, `DeviceKeyboard.swift`, and the PRD threat model. The PRD excludes process injection, modified binaries, root, and malicious hardware. It includes same-user agents with Accessibility and Screen Recording grants. It defers uploads, downloads, printing, media permissions, external handoff, and third-party sign-in flows.

WebKit links below point to current upstream source. The installed macOS framework can differ. Every behavior needs a live test on the frozen app before it supports a prevention claim. An app-internal responder call proves an implementation path exists. It does not prove an external agent can invoke it.

## Highest priorities

### 1. Disable Writing Tools with public API

**Source:** Apple says `WKWebView` defaults to the limited Writing Tools experience. `WKWebViewConfiguration.writingToolsBehavior = .none` opts out. The macOS API exists from macOS 15. [Apple WWDC24, 7:11 to 8:16](https://developer.apple.com/videos/play/wwdc2024/10168/), [configuration property](https://developer.apple.com/documentation/webkit/wkwebviewconfiguration/writingtoolsbehavior).

**Local gap:** The browser does not set this property. `DeviceFieldEditor` also inherits `NSTextView` behavior.

**Implementation:** Set `.none` before web view creation. Set `.none` on the field editor too. Then test selected text and editable content for Writing Tools commands. This restriction applies across pages without injected JavaScript.

### 2. Cover native export responders and context menus

**Source:** WebKit implements `copy:`, `cut:`, `paste:`, `pasteAsPlainText:`, and selection commands as native responder methods. It also implements `writeSelectionToPasteboard:types:`, `readSelectionFromPasteboard:`, and `validRequestorForSendType:returnType:`. These methods call WebKit directly. [WKWebViewMac.mm, native responders](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm#L247).

**Source:** Services use the requestor to export selected text and to import a replacement through a pasteboard. [Apple Services requestor](https://developer.apple.com/documentation/appkit/nsservicesmenurequestor), [Apple selection export](https://developer.apple.com/documentation/appkit/nsservicesmenurequestor/writeselection(to:types:)).

**Source:** WebKit builds native context menus, including Services and Share. Its Share item can contain selected text or image data. It can create a synthetic event and call `NSMenu.popUpContextMenu` directly. [WebContextMenuProxyMac.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebContextMenuProxyMac.mm#L436).

**Local gap:** Removing the Edit menu and refusing drag imports leaves these inherited methods intact. `AXBoundaryWebView` overrides AX and drag methods, but no export responders.

**Implementation:** Deny deferred copy/cut/paste and Services import/export in the protected web view and field editor. Return no Services requestor. Test direct native selector entry separately from key events. A `menu(for:) = nil` override alone is insufficient evidence because WebKit constructs menus internally. The inspected macOS context-menu customization callbacks are private SPI. [WebKit delegate declarations](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKUIDelegatePrivate.h).

### 3. Measure Web Share and WebAuthn as separate UI boundaries

**Source:** `WebViewImpl::showShareSheet` creates `WKShareSheet` and presents page-supplied data. [WebViewImpl.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm#L2983). Upstream enables Web Share on supported Cocoa platforms. [WebKit preferences](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml#L6999).

**Inference:** A page request after physical activation can create native sharing UI. The existing application event gate does not itself deny that request. This needs a live `navigator.share` test, including attempts to operate the resulting native UI externally.

**Source:** Upstream also enables Web Authentication. Its modern request route calls AuthenticationServices through `ASCAgent`. Other configurations use the authenticator manager and a native presenter. [WebKit preferences](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml#L6563), [WebAuthenticatorCoordinatorProxy.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/WebAuthentication/WebAuthenticatorCoordinatorProxy.cpp#L151), [AuthenticatorManager.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/WebAuthentication/AuthenticatorManager.cpp#L181).

**Local gap:** The browser has no explicit Web Share or WebAuthn policy. The inspected public `WKUIDelegate` header offers no general macOS denial callback for either feature. The old WebAuthn callback in the private header does not cover every modern path. [Public delegate header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKUIDelegate.h).

**Implementation decision:** Keep these routes unresolved until live tests show denial. Do not label absent delegates as prevention. The engine controls below suit a separate research build. They change the PRD's public-API-only design.

## Engine controls for a separate research build

**Source:** The private `WKPreferences` interface declares `+_features`, `-_setEnabled:forFeature:`, and `-_isEnabledForFeature:`. `_WKFeature.key` gives the engine key. These are private SPI, even when called through standard Objective-C dispatch. [Preferences header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKPreferencesPrivate.h#L130), [feature object](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/_WKFeature.h).

**Source:** The generator includes all exposed Boolean preferences in the feature catalog. It includes mature and embedder controls. The narrower experimental catalog excludes those statuses. [Preference generator](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/GeneratePreferences.rb#L318).

| Engine key | Upstream default | Research restriction |
| --- | --- | --- |
| `WebShareEnabled` | True on supported Cocoa platforms | Disable native Web Share requests. |
| `AsyncClipboardAPIEnabled` | True on supported Cocoa platforms | Disable the async Clipboard interface. Native Copy, Services, and legacy editing need separate restrictions. |
| `WebAuthenticationEnabled` | True when compiled | Disable the Web Authentication interface. |
| `ApplePayEnabled` | True with remote payment UI, otherwise false | Disable Apple Pay. |

These exact keys and defaults appear in [WebKit's preference definitions](https://github.com/WebKit/WebKit/blob/main/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml). The Clipboard and Credentials interfaces use their corresponding settings. [Clipboard.idl](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/async-clipboard/Clipboard.idl), [CredentialsContainer.idl](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/credentialmanagement/CredentialsContainer.idl).

**Source:** `_setApplePayEnabled:` and `_applePayEnabled` are dedicated macOS SPI. The inspected source does not declare dedicated Web Share, async Clipboard, or Web Authentication setters. `_setApplePayCapabilityDisclosureAllowed:` only changes the separate disclosure preference. [Preferences header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKPreferencesPrivate.h#L200), [Preferences implementation](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKPreferences.mm).

**Recommendation:** Check selector availability on the installed framework. Enumerate `+_features` and match exact keys. Set false through `-_setEnabled:forFeature:` and read back through `-_isEnabledForFeature:` before creating the web view. Repeat the checks on the web view's effective configuration. Refuse page loading if a required selector or key is missing, or a readback is true. Do not infer denial from a false getter for an unknown key. The upstream getter returns false when no key matches. [Feature implementation template](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/Scripts/PreferencesTemplates/WebPreferencesFeatures.cpp.erb#L52).

The installed catalog and readback remain untested in this research note. Web-visible interface checks and native UI tests must follow readback. A stored false preference alone does not prove that every UI route honors it.

`PaymentRequest.idl` explicitly uses `EnabledBySetting=PaymentRequestEnabled`. This key did not appear in the inspected unified preference definitions. Its presence in the installed feature catalog remains unresolved. Follow-up source review found that `WebPage::updateSettings` assigns PaymentRequestEnabled from the ApplePayEnabled preference. The separate catalog key is therefore not required by that upstream implementation. The installed catalog omitted it, and the first strict diagnostic correctly refused startup. The revised policy requires ApplePayEnabled and checks interface exposure separately. Installed behavior still needs measurement. [WebPage settings](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/WebProcess/WebPage/WebPage.cpp#L5134). [PaymentRequest.idl](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/paymentrequest/PaymentRequest.idl). `PaymentHandler.cpp` includes Apple Pay and Apple Pay AMS handlers. [PaymentHandler.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/paymentrequest/PaymentHandler.cpp). Tests must stop before payment completion.

## Remaining feature checks

| Feature | Source behavior | Local gap and action |
| --- | --- | --- |
| JavaScript alert, confirm, prompt | Without delegate methods, upstream completes alert, returns false for confirm, and returns null for prompt. It does not create a default dialog. [UIDelegate.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Cocoa/UIDelegate.mm#L389) | Add explicit handlers with these results and visible unsupported-operation feedback. Preserve the completion-handler contract. Test main frames and iframes. |
| New windows | The automatic-window preference only controls opening without user interaction. The creation callback returns a new web view or nil. [Apple preference](https://developer.apple.com/documentation/webkit/wkpreferences/javascriptcanopenwindowsautomatically), [WebKit delegate header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKUIDelegate.h#L78) | Current callback loads any allowed popup request in the existing view before returning nil. Reject popups visibly, or define a shared navigation policy that also checks downloads and target-frame intent. |
| Response downloads | `shouldPerformDownload` describes a web-content attribute, so it is not a complete response policy. The response delegate can allow, cancel, or download. Without it, upstream allows displayable MIME types and ignores others. [Apple attribute](https://developer.apple.com/documentation/webkit/wknavigationaction/shouldperformdownload), [NavigationState.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Cocoa/NavigationState.mm#L729) | Add response checks for allowed URL, displayable MIME, and attachment disposition. Cancel unexpected `didBecomeDownload` objects through both action and response callbacks. Do not retain resume data. [Apple cancellation](https://developer.apple.com/documentation/webkit/wkdownload/cancel(_:)) |
| File chooser | Passing nil to the open-panel completion cancels WebKit's listener. [UIDelegate.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Cocoa/UIDelegate.mm#L826) | Already explicit. Test single/multiple files, directory input, iframe input, and keyboard activation. |
| Printing | The inspected WebKit client only calls its print delegate when implemented. It otherwise completes without displaying print UI. App code can separately create an `NSPrintOperation`. [UIDelegate.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Cocoa/UIDelegate.mm#L1372), [Apple print API](https://developer.apple.com/documentation/webkit/wkwebview/printoperation(with:)) | There is no app print command. Test `window.print()` and inherited responder/embedded PDF controls. Do not add a default print panel. |
| Authentication challenges | Without a challenge delegate, current upstream rejects the protection space and continues. [NavigationState.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/Cocoa/NavigationState.mm#L1082) | Add explicit policy if supported HTTP authentication becomes necessary. Keep valid server-trust handling separate from HTTP Basic, Digest, and client-certificate credentials. Never accept invalid trust. |
| Fullscreen | The public preference defaults false. When true, fullscreen removes the web view from the app hierarchy. [Apple fullscreen preference](https://developer.apple.com/documentation/webkit/wkpreferences/iselementfullscreenenabled) | Set false explicitly. Test video fullscreen and Picture in Picture separately because they can use other presentation paths. |

## Cross-page acceptance

Use a fixture for each feature, then repeat external AX, capture, and input attacks while its native UI is present. Include subframes, redirects, new-window requests, process recovery, and embedded PDF content. A blocked request on one page does not cover a different feature implementation.

Keep human compatibility evidence separate. A page that cannot receive either physical input or agent input does not establish a usable agent-free browser.
