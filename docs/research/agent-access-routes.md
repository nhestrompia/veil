# Screenshot capture and protected rendering

Research date: October 27, 2026. Sources are official Apple and Playwright documentation.

## Screenshot files are optional

Playwright's `page.screenshot()` returns a `Buffer`. Its `path` option is optional. The API states that omitting `path` means the image does not save to disk. The screenshot guide shows the returned buffer converted to base64. An agent can therefore receive screenshot bytes without a screenshot file. [Playwright screenshot API](https://playwright.dev/docs/api/class-page#page-screenshot), [capture into buffer](https://playwright.dev/docs/screenshots#capture-into-buffer).

macOS also exposes capture data directly. `SCScreenshotManager.captureImage(contentFilter:configuration:)` returns a `CGImage` through its asynchronous result or completion handler. `SCStreamOutput` receives frames as `CMSampleBuffer` objects and can retrieve image data from those objects. Neither API signature requires an output file. [Apple screenshot API](https://developer.apple.com/documentation/screencapturekit/scscreenshotmanager/captureimage(contentfilter:configuration:completionhandler:)), [Apple capture stream output](https://developer.apple.com/documentation/screencapturekit/scstreamoutput).

Inference: a watcher for PNG files, the Desktop, or temporary folders cannot cover these capture routes. The watcher receives no file event when the agent keeps the image in memory. A file event also follows file creation. Detection at that point does not establish that the image remained private. Such a watcher can supply diagnostic evidence for tools that save files, but it cannot enforce capture prevention.

## What the protected layer promises

Apple describes `AVSampleBufferDisplayLayer` as a layer that displays compressed or uncompressed video frames. Its `preventsCapture` Boolean controls whether the layer protects against screen capture. This is an explicit capture-protection API. The cited property documentation does not specify a complete matrix of capture methods or a human-visible result for arbitrary HTML. [Apple display layer](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer), [Apple capture property](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer/preventscapture).

FairPlay Streaming protects encrypted streaming media delivered through HTTP Live Streaming. Its system includes content encryption, key exchange, and protected playback. This scope differs from setting a capture flag on an uncompressed display layer. FairPlay's public overview does not establish that the system can protect an arbitrary interactive HTML document. [Apple FairPlay Streaming](https://developer.apple.com/streaming/fps/), [Apple FairPlay troubleshooting](https://developer.apple.com/library/archive/technotes/tn2454/_index.html).

Inference: rendering HTML into video and protecting that video remains a separate experiment. The conversion, encryption, protected playback, and input bridge need evidence. These sources do not prove that such a browser is impossible. They also do not supply a complete browser design.

## Implications for this project

The project should test capture prevention where the operating system produces captured pixels. Watching where agents save images does not cover captures held in memory.

A useful protected-rendering result needs both a visible page on the physical display and hidden page content in the tested capture methods. A black physical display fails that requirement even if screenshots are black.

Capture protection addresses visual observation. It does not establish that the browser blocks external JavaScript evaluation, semantic reads, accessibility actions, or synthetic input. Those routes need separate checks.

## Evidence limits

This note describes public API contracts. It does not report a new live test on this Mac. The Apple property documentation gives limited detail about capture coverage. No universal capture notification or interception mechanism follows from the sources above. The file-watcher limitation follows from the documented routes that return data directly in memory.

## Agent routes and current implementation

Browser automation and desktop automation need separate defenses. Playwright MCP can read structured accessibility snapshots, act on element references, and evaluate page JavaScript. Screenshot blocking does not stop those operations when their browser connection remains available. [Playwright MCP](https://playwright.dev/docs/getting-started-mcp), [Playwright code execution](https://playwright.dev/mcp/tools/code-execution).

The shell sets `isInspectable=false` outside the inspection control. Apple documents this switch for Safari Web Inspector access. The existing live test found the control available and the candidate absent from the inspector menu. That result is narrower than universal debugger-attachment prevention. See [the shell](../../Sources/Browser/BrowserApp.swift), [inspector findings](../safari-remote-findings.md), and [Apple inspection guidance](https://developer.apple.com/documentation/safari-developer-tools/enabling-inspecting-content-in-your-apps).

The mouse work is an offline feature and replay pilot. It contains one user-declared physical trace and fifteen synthetic sessions. The physical baseline remains unverified. No trained classifier or active browser behavior gate exists. The copied trace preserves the selected features exactly. This is an offline limitation, not a successful live evasion. See [mouse findings](../behavior-replay-findings.md) and [the analysis tool](../../tools/behavior_replay.py).

No keyboard behavior classifier exists in this implementation. The separate keyboard experiment derives accepted events from a selected device and rejects ambient application events. This is a source policy. It does not infer human behavior from typing rhythms. The experiment disables mouse input. See [keyboard routing](../../Sources/Browser/DeviceKeyboard.swift).

Both uncompressed protected-layer configurations produced black output on the physical display. Their matched unprotected control remained visible. These configurations therefore fail useful capture protection. They were not complete FairPlay implementations. See [pixel findings](../pixel-rendering-findings.md).

## Focus for the next experiment

Keep direct script access, operating-system accessibility, visual capture, and synthetic input as separate rows in one attack matrix. Record observation and completed website actions separately. Preserve ordinary website JavaScript while denying outside automation access.

Prioritize a physically visible protected-rendering control before adding a browser interface around that path. Compare window capture, full-display capture, and continuous capture with matched readable controls. Only then test interaction, resize, fullscreen, and fresh website content.

Keep behavior detection as a measured resistance experiment. Evaluate generated trajectories, independent human-trace replay, keyboard-only attacks, and accessibility actions. Report human task completion and false blocks alongside agent success. Do not promote the offline pilot into a claim of human-origin proof.

Do not add a screenshot-file watcher as a capture-prevention mechanism. Further signal-isolation work is not the priority for this question. No new privileged experiment, permission, global input hook, or live capture ran for this note.
