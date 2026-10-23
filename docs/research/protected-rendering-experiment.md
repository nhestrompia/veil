# Protected-rendering experiment

Status: a public-API HTML-to-pixel candidate now compiles. Capture resistance, human visibility, and interaction remain unverified. No Chromium modification exists. See the [candidate findings](../pixel-rendering-findings.md).

## Question and separation from the MVP

Can a browser render arbitrary, interactive HTML through a graphics path that excludes the content from relevant macOS capture methods?

This track preserves the DRM hypothesis separately from the WKWebView shell. It does not assume that encrypted video can protect adjacent HTML. It also does not assume that a graphics path suitable for protected media accepts arbitrary application pixels.

The initial native-input and screenshot experiments come first. Continue this track only after identifying a concrete capture route, a plausible protected graphics path, and a useful result to test. Keep engine changes and their maintenance cost outside the initial 2 to 3-day budget.

Capture resistance and input resistance remain separate. A protected image can still expose a known layout to blind input attempts. This experiment cannot substitute for native-input or accessibility tests.

## Existing evidence

Antiagent's transparent encrypted overlay did not hide the underlying canvas in the documented Chrome captures. Encoding the interface inside encrypted media omitted it from some captures. Compositor screenshots still recovered the interface. That fixture contained a prerecorded interface, not interactive HTML.

These are route-specific historical observations. Some historical image artifacts are absent from the current Antiagent checkout. See the [Antiagent review](antiagent-review.md) for the evidence status and links to findings and JSON records.

Current macOS window-sharing flags do not establish protection for arbitrary browser content. The [platform research](browser-feasibility.md) cites the relevant Apple and Electron documentation. A working media path is not evidence for a protected HTML path.

## Questions before a renderer build

1. Where does the candidate path mark content as protected, and which component enforces that property?
2. Can that path accept arbitrary HTML output without an accessible clear copy or an intermediate readable screenshot?
3. Do compositing, scaling, resizing, fullscreen, and additional displays preserve the property?
4. Can the person scroll, type, select text, focus controls, and use dynamic pages with acceptable latency?
5. Which capture and export methods still recover content, and what does each successful capture actually copy?

Start with a source-level map of the content producer, graphics buffers, compositor, and capture entry points. Pin the engine revision and document public API support. An unsupported technique needs an explicit research scope decision before implementation.

## Test matrix

| Dimension | Cases | Required observation |
| --- | --- | --- |
| Content | Static HTML, canvas, changing text, text fields, scrolling, iframe content, and a dynamic web app. | Real interactive content reaches the candidate path. A prerecorded video is only a media control. |
| Capture | ScreenCaptureKit window and display capture, system screenshots, recording or sharing, and any exposed engine capture path. | Save actual images and decoded frames. Record readability for each independent path. |
| Composition | Resize, zoom, fullscreen entry and exit, display-scale changes, overlays, menus, and popups. | No readable intermediate frame or unrestricted secondary window appears. |
| Interaction | Pointer and keyboard actions, text editing, scroll, drag, focus, and supported accessibility. | People complete the same tasks. Record compatibility and latency. |
| Recovery | Navigation, process recovery, protected-path failure, and relaunch. | The browser never silently falls back to an unprotected path under a protected claim. |
| Alternative reads | Accessibility, clipboard, print, DOM inspection, and any retained clear buffers. | Report surviving routes independently. Protected pixels alone cannot establish agent-free behavior. |

Pair each protected case with the same content through an unprotected path. Use fresh fake secrets and harmless actions. Confirm human readability at capture time, not from the captured image. A black capture caused by a failed renderer is inconclusive.

Save raw evidence, configuration, environment, source revision, errors, latency, and human observations. Inspect transitions as well as stable frames. Failed capture permissions and absent windows never count as protection.

## When to consider Chromium changes

Consider a fork only when source analysis identifies a specific missing producer, protected-buffer property, or compositor/capture check. The proposal must identify a patch to test and a route it could close. It must also name the routes outside that patch's authority.

Do not fork merely because WKWebView accepts CGEvent input or macOS captures its window. Those observations do not establish that another engine changes the outcome.

The smallest useful result is a reproducible, route-specific protected HTML path with real interaction. A production renderer, complete Chromium fork, and arbitrary-site compatibility remain separate work.

## Decisions

Continue if the matched controls show real HTML capture exclusion while people retain useful interaction. Scope the result to the exact OS, build, content, and capture paths.

Keep a media-only result separate if it cannot carry HTML. Stop the candidate if unprotected copies defeat it, required captures remain readable, or human usability makes it unsuitable. Preserve the negative evidence instead of returning to overlay tuning.
