# macOS browser resistance to agent tools

Draft for publication, 2026-10-28. The tested MVP is not agent-free. It resists several measured input and observation methods, but app activation causes website actions in a crafted page on the unchanged preview.

## Scope and claim

The project tests a minimal macOS WKWebView browser that limits external observation and admits a measured physical keyboard route. The target is an ordinary-user agent with available macOS grants. Root, modified browser images, kernel exploits, malicious hardware, external cameras, and an agent's separate browser are outside this PoC.

The primary agent is gpt-6.1-sol through Codex in T3 Code. A subagent independently attempts the Wikipedia task. Tools include native computer use, the permissioned NativeProbe, Playwright controls, renderer Accessibility probes, and ScreenCaptureKit recorders. This is a capability-based test of those recorded implementations. It is not a benchmark of every current agent model.

The central candidate image has SHA-256 `dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70`. Results from older diagnostic apps are explicitly separate. Human controls establish visible pages and physical operation on the relevant candidate processes. Failed permissions, failed controls, and missing frames never count as protection.

## Results by method

| Method | Observed result | Limit |
| --- | --- | --- |
| Focus-only app activation | Three new accepted actions in three cycles on the actual preview | Crafted focus-sensitive page, armed by a human first |
| Blind native input on public pages | A calibrated directed key-code route leaves Google, Wikipedia, and GitHub search fields unchanged | User confirms final state. Four additional Google routes lack successful controls |
| Independent agent repeat | Subagent's Wikipedia attempt also leaves the field empty | Same native route, not a separate automation technology |
| Native computer-use client | Searches succeed in readable public-page references. Preview binding times out | Client binding failure supplies no confirmed candidate action |
| Native Accessibility | Host and window metadata remain visible. Tested page controls and marker are absent | Bounded methods, not every possible semantic read |
| Renderer Accessibility | One token-read comparison recovers the reference marker and no preview marker | Other read methods fail their controls |
| Scoped screenshots | Completed window captures are black with readable controls | Does not cover unfiltered full-display capture |
| Independent-window streaming | 948 delivered complete preview frames are black, with readable controls before and after | Applies to that stream, not undelivered frames or all transitions |
| Unfiltered display streaming | Fullscreen readable control passes all three filter stages | Actual preview capture refuses overlap before pixels. Candidate remains inconclusive |
| External HTTPS and JavaScript URLs | GitHub session explicitly refuses both external-open attempts | Does not test debugger attachment |
| Playwright | Isolated Chromium controls read pages and complete tasks | CDP and Playwright WebKit are not supported attachment methods for an arbitrary WKWebView |
| External scripted Web Inspector | Current client cannot pass its readable reference | No current candidate prevention claim |
| Behavior classifier | Offline mouse replay research only | No trained live classifier or adaptive evasion result in this MVP |

Sources for these local measurements are the [loaded public-page findings](loaded-public-website-findings.md), [physical preview controls](preview-session-findings.md), [native input findings](preview-native-input-findings.md), [renderer reads](preview-renderer-live-findings.md), [stream results](preview-stream-live-findings.md), and [focus bypass](preview-focus-action-findings.md).

## The successful attack

After a human arms the local fixture, an ordinary-user helper switches app focus away and back. Each of three cycles causes one additional server-accepted action in the unchanged preview. Each stationary control records zero new actions. The browser logs zero admitted input events during the cycles.

The helper sends no keyboard, mouse, or Accessibility action. It does not inject page code or post an action request. The page's pre-existing JavaScript focus handler sends the request. This is an agent-controlled page action through the browser, despite the input gate.

The result defeats the broad requirement that agents cannot cause actions on any website. It does not show that an agent can complete a normal Google search or read an arbitrary protected page. The [raw evidence](evidence/preview-focus-action-results.json) records process identity, controls, oracle snapshots, hashes, and cleanup. Its limits include user-attested physical inactivity and an oracle without authenticated browser-process attribution.

## What screenshot protection establishes

Black output is evidence for a specific working capture method when the human can see the same page. Earlier protected-video experiments sometimes also appear black on the physical display. Those trials fail usability and do not establish capture protection.

Apple now describes `NSWindow.SharingType.none` as a legacy constant and says not to use it to hide captured content. Its linked FairPlay documentation concerns streaming media. It does not promise protected rendering of arbitrary interactive HTML. [Apple window policy](https://developer.apple.com/documentation/appkit/nswindow/sharingtype-swift.enum/none), [FairPlay Streaming](https://developer.apple.com/streaming/fps/)

A screenshot-file watcher cannot cover clients that return screenshot bytes from memory. The client implementations must be tested directly. Agent tools can also use semantic trees, browser scripts, or blind input. [OpenAI computer use](https://developers.openai.com/api/docs/guides/tools-computer-use), [integration examples](https://developers.openai.com/api/docs/guides/tools-computer-use-integration)

## What is missing before release acceptance

The demonstrated focus route needs an integrated defense that preserves physical browsing. Other lifecycle and timing routes need tests on the same final build. Successful separate experiments do not count as integrated protection.

Unfiltered display capture still needs a complete candidate comparison with readable references and valid privacy coverage. External inspector scripting still needs a working reference. Keyboard observation needs a preview-specific result. Appium Mac2 has not been tested. Its Xcode and Accessibility requirements remain separate prerequisites. [Mac2 documentation](https://appium.github.io/appium-mac2-driver/latest/getting-started/)

The candidate supports a measured built-in keyboard and US ASCII. Mouse input is disabled. Unicode, input methods, broad website compatibility, and the PRD's human-use targets remain unmet. These usability limits cannot count as defenses.

The present evidence supports a report on measured resistance and a reproducible bypass. It does not support publishing this build as an agent-free MVP. The [gap audit](agent-free-gap-audit.md) tracks the remaining acceptance work, and the [method research](research/publication-agent-methods.md) explains the supported agent interfaces.
