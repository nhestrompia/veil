# Content policy across page features

The new source policy disables native sharing, asynchronous clipboard access, WebAuthn, and Apple Pay in the WebKit configuration. Three fresh diagnostic processes exposed sharing, clipboard, and WebAuthn in readable views. Protected views exposed none of those interfaces. All effective preference readbacks passed. This is an engine configuration result, not an external attack result.

## Implementation

Protected views disable Writing Tools and element fullscreen. The address editor also disables Writing Tools. A restricted WKWebView subclass refuses copy, cut, paste, print, native selection export, and Services requests. Context-menu entry methods return no menu or action. WebKit can synthesize native menus internally, so these overrides do not establish complete context-menu prevention.

The navigation response policy cancels attachments, undisplayable MIME types, and disallowed URLs. Both download-conversion callbacks cancel unexpected downloads. Existing upload and media refusals remain in place.

Four private WebKit feature keys control sharing, asynchronous clipboard, WebAuthn, and Apple Pay. The policy enumerates exact keys, disables them, and reads them back. Missing selectors, missing keys, or enabled values refuse startup. It repeats readback on the created view's effective configuration. This private API is an experimental dependency and can change with macOS.

The first calibration required a separate PaymentRequestEnabled key. The installed catalog omitted it, and startup correctly failed. Upstream WebKit maps PaymentRequestEnabled to ApplePayEnabled during settings updates. The revised policy requires the Apple Pay key. Payment APIs were absent in both readable and protected views, so this experiment provides no positive payment-interface control. [WebKit settings implementation](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/WebProcess/WebPage/WebPage.cpp#L5134).

The public Writing Tools property is hidden by this SDK at a macOS 14 deployment target. The policy checks its public Objective-C selectors, sets the value, and reads it back on macOS 15 and later. No JavaScript replacement implements these restrictions.

## Live diagnostic results

| Check | Result |
| --- | --- |
| Sharing, clipboard, WebAuthn interfaces | Present in all three readable views, absent in all three protected views |
| Four effective feature values | Disabled in all three protected views |
| Unknown required feature | Startup refused in all three runs |
| Writing Tools and element fullscreen | Disabled |
| Native selection export | Inconclusive. The readable writer returned success but exported an empty string |
| Private authorized keyboard task | One accepted task with the new source policy |
| Temporary process cleanup | Passed |

Both views held a selection containing the fixed fake marker. The protected writer returned false and preserved its named pasteboard. The readable writer failed to export the marker, so the controller does not count export prevention. Services requestor calibration also failed. The diagnostic used only unique named pasteboards. It did not read or write the general clipboard.

An earlier page check raced the initial blank document. Its interfaces were not a valid reference. The revised diagnostic waits for the fixed marker before observation. The saved evidence retains this failed readiness control.

## Scope and compatibility

The policy applies to each document in the configured view, rather than a website-specific script. Frame and page-feature coverage still needs its own tests. Disabling these features also disables passkey authentication, native sharing, and related human workflows. Generic compatibility with every website is unproven.

The physical browser remains PID 61893 with its earlier binary. Only separate diagnostic apps contain the new source policy. Its successful private keyboard sequence is not a new physical-human control. No system permission changed. No global input hook was installed.

[Saved results](evidence/content-policy-results.json) retain three matched interface comparisons, failed controls, identities, and cleanup. [The source review](research/page-feature-boundaries.md) lists further native UI paths. The browser is not proven agent-free.
