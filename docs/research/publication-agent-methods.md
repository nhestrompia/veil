# Agent methods and publication limits

Research date: 2026-10-28. This review uses current primary documentation and the project's linked local evidence. The later milestone 151 focus result is recorded separately.

Publish measured resistance to named agent capabilities. The available evidence does not support an absolute agent-free claim. A working public page, a working attack reference, and an independent outcome check are separate requirements.

## What current agent tools need

| Tool or method | Supported connection | Meaning for this browser |
| --- | --- | --- |
| Playwright `chromium.connectOverCDP` | Chrome DevTools Protocol on a Chromium browser | It cannot establish a supported attachment to a system WKWebView. A refused localhost connection proves no WKWebView defense. |
| Playwright `webkit.connect` | A Playwright endpoint from `BrowserType.launchServer` | It does not attach to an arbitrary AppKit process by PID. Launching a separate Playwright WebKit instance tests that instance. |
| Safari Web Inspector | An inspectable WKWebView listed in Safari's Develop menu | This is the relevant documented WebKit inspection route. A working readable reference must precede comparison. |
| Safari WebDriver | The Safari version associated with `safaridriver` | A Safari search does not operate the research browser. It supplies a separate automation reference. |
| Computer-use agent | A client implementation that captures images and sends mouse or keyboard actions | Test the actual macOS capture and input implementations, with effective permissions. A model name alone does not define those capabilities. |
| Browser-use agent | A client implementation that reads page structure and executes page actions | Test its actual connection to this WKWebView. A DOM tree from another browser does not count. |
| Appium Mac2 | Apple's XCTest framework for macOS apps | This supplies an additional native automation method. It has separate Xcode and Accessibility prerequisites. |

Playwright documents the first two connection contracts. Its WebKit builds contain patches, and it does not support branded Safari. Passing `AgentFreeBrowserPreview` as an executable does not create the required automation implementation. This is an interpretation of those contracts, not a measured security result. [Playwright BrowserType](https://playwright.dev/docs/api/class-browsertype), [Playwright browser support](https://playwright.dev/docs/browsers)

WebKit documents `isInspectable` as a per-view switch. It defaults to false. Disabling it closes an active inspection session. Safari's Develop menu is the documented client workflow. The packaged browser sets it to false. This documents the intended inspection policy, not proof against every debugger. Apple's WebDriver documentation limits each `safaridriver` to its associated Safari version. [WebKit inspection API](https://webkit.org/blog/13936/enabling-the-inspection-of-web-content-in-apps/), [Apple Safari WebDriver](https://developer.apple.com/documentation/webkit/testing-with-webdriver-in-safari), [browser source](../../Sources/Browser/BrowserApp.swift)

Official OpenAI documentation distinguishes screenshot-based computer tools from browser tools that read page text and controls. The application supplies the driver and executes actions. Its examples also allow code that uses Playwright or PyAutoGUI. Thus, testing one screenshot method does not cover every implementation. [OpenAI computer use](https://developers.openai.com/api/docs/guides/tools-computer-use)

Anthropic documents a desktop screenshot-and-input loop and a separate browser loop. The browser loop can expose accessibility trees, forms, tab state, screenshots, and optional JavaScript execution. The client implements those operations. This supports testing both visual and semantic access. It does not establish a connection to arbitrary WKWebView apps. [Anthropic computer use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool), [Anthropic browser use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)

Appium's Mac2 documentation describes XCTest-based macOS automation. It requires Xcode and Accessibility access for its helper. Record an unmet prerequisite as unavailable. Do not count it as a browser block. [Appium Mac2 source](https://github.com/appium/appium-mac2-driver), [current Mac2 prerequisites](https://appium.github.io/appium-mac2-driver/latest/getting-started/)

## Capture protection has no general guarantee here

Apple currently calls `NSWindow.SharingType.none` a legacy constant. Its documentation explicitly says not to use it to hide captured content. It points developers to FairPlay Streaming. FairPlay protects streaming media delivered through HTTP Live Streaming. That documentation does not establish protection for an arbitrary interactive HTML interface. [Apple window-sharing policy](https://developer.apple.com/documentation/appkit/nswindow/sharingtype-swift.enum/none), [FairPlay Streaming](https://developer.apple.com/streaming/fps/)

Black scoped screenshots remain valid observations for their exact capture methods. They cannot establish protection against an unfiltered display stream. Test captures before page display and after display. Include filter changes, resize, fullscreen, focus changes, and the first complete frame. Keep a readable reference before and after each comparison.

A screenshot-file watcher cannot cover every computer-use implementation. For example, OpenAI's examples return screenshot bytes to the agent loop. No saved screenshot file is required. This is a design inference from the example, not a local bypass result. [OpenAI computer-use integration](https://developers.openai.com/api/docs/guides/tools-computer-use-integration)

## What the local trials establish

The [loaded-page findings](../loaded-public-website-findings.md) record physically visible Google, Wikipedia, and GitHub pages in the pinned preview image. The user reports empty fields after the attempts. Directed native input submits the phrase in matched references. The preview exposes no page controls through native Accessibility. Scoped captures are black. External search and JavaScript URLs receive explicit refusals.

Those results cover the recorded methods and sessions. They do not show that a current computer-use client successfully binds to the preview. That binding times out. External inspector attachment also lacks a working scripted reference. Milestone 151 now demonstrates a [focus action bypass in the actual preview](../preview-focus-action-findings.md). Unfiltered candidate capture and other lifecycle or timing methods remain open. See the [gap audit](../agent-free-gap-audit.md).

## Concrete next experiments

1. Run the available computer-use client against a loaded public page in the pinned preview. First prove its observations and search action in the readable app. Keep binding failures separate from action refusals.
2. Test blind input and native Accessibility actions on the same loaded page. Give the agent the layout from the reference. This tests action prevention when secrecy fails.
3. Complete unfiltered ScreenCaptureKit capture with readable references. Use an owned backdrop and a fixed public-page crop. Refuse capture when unrelated windows overlap it.
4. Get one scripted inspector client to read a fresh marker and run a harmless action in the readable WKWebView. Then compare the unchanged preview. Do not substitute a missing TCP listener.
5. Test an integrated defense against the demonstrated focus bypass, then repeat other lifecycle and timing fixtures. A script already on the page can react without synthetic input.

Each attempt record needs the binary hash, OS build, process ID, agent model, client version, permissions, action transcript, budget, and outcome evidence. Check human usability in that same session. Keep public-site searches separate from the private fixture's server-confirmed actions.

## A defensible published claim

The current result supports this statement:

> On the recorded macOS build and browser image, several measured native-input and capture methods failed. A human-armed local page nevertheless completed three new server-accepted actions when an agent changed app focus. The helper posted no keyboard or mouse events. This build is not agent-free.

Do not say all agents, all websites, or no future bypass. Three public websites test practical use. They do not prove a universal security property. A fresh private marker tests disclosure. An independent task oracle tests actions. Both are necessary, and neither replaces the other.
