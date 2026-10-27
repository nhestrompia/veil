# Agent attack inventory

This inventory separates attempted routes from remaining work. It does not enumerate every possible future attack. The current protected target is PixelKeyboardExperiment. Earlier pixel-only findings remain identified separately.

| Agent method | What the agent tried | Result and scope |
| --- | --- | --- |
| Screenshot plus vision | Native window, filtered display, and system-window captures of fresh pages | Earlier H.264 target omits content while the clear control is readable. The agent visually checked saved images and corrected an OCR alias error. |
| Accessibility text | Host tree, focused-element reads, and hit tests | Earlier pixel target reveals no page marker. The new host returns one application root. Direct new-host queries fail foreground calibration. |
| Accessibility actions | Set the fixture field and press its button | Works in the ordinary reference. Pixel-only controls are absent. Loaded-page actions in the new browser remain untested. |
| Browser protocol | Real Playwright/CDP attachment and DOM/form operations | Works in isolated Chrome. Requested native debugging ports refuse connections. Other inspection transports remain untested. |
| Launch arguments | Supply a URL whose page records an action on load | Completed actions in the old protected app. New device-gated startup sends no page-ready event or action. |
| External URL opening | Send a URL to the running combined app | The new delegate explicitly refuses. No page-ready event or action follows before enrollment. |
| Native mouse and keyboard | Planned CGEvent, HID-state, curved, directed, and blind attempts | Not run in this audit because modifying mouse hooks are active. The new app also lacks its physical baseline. |
| Computer-use adapter | Earlier native tool invocation | It returned after the timed trial and opened an empty app. Invalid observation, not a block. Current model-directed image/AX attempts use the scoped native probe. |
| Continuous and unfiltered capture | ScreenCaptureKit stream and whole-display methods | Still require a calibrated adapter with safe research-only coverage. No blocked result exists here. |
| Renderer accessibility | Query WebKit processes independently | The frozen helper rejects unrelated host identities. A reviewed expanded scope is needed. |
| Clipboard, printing, downloads, and popups | Existing restrictions reused in the combined app | Source-level restrictions are present. New live export trials remain necessary after physical enrollment. |
| Focus, visibility, resize, timers, and process pause | Earlier project trials found zero-input actions | Not retested or solved by this integration. Signal isolation remains separate. |
| Direct website APIs outside this browser | Independent HTTP or another browser session | Outside the agreed browser boundary. The oracle is used only to score tests. |
| Modified binaries, root, kernel changes, and external cameras | No attempt in this audit | Outside the agreed PoC threat model. |

The first physical test of the frozen combined image fails. Its protected page is black, while the clear control is visible. See [physical findings](pixel-keyboard-physical-findings.md). No detector accuracy or universal agent-blocking rate follows from these observations.
