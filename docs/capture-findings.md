# Capture and browser-automation findings

Milestone 3, October 23, 2026. The current shell remains usable by permissioned native agents.

## Screenshot-driven operation

The screenshot/OCR/native-input client completed 3/3 protected-browser trials and 3/3 inspection-enabled control trials. Its observation route used ScreenCaptureKit images and local Vision OCR. It used CGEvent input with a curved pointer path. It did not read an AX tree, DOM, or browser-content API.

OCR located the visible field label. The client derived the field position from that label and the public fixture's fixed spacing. This is an adaptive observation of the current window, but not a demonstration across arbitrary unseen layouts.

Both ScreenCaptureKit window capture and the system window screenshot command produced readable page images. Exact OCR recovered the fresh marker in 4/6 trials for each capture method. Two protected-browser markers contained OCR substitutions between zero and the letter O. Those mismatches do not establish capture protection. All six task actions still completed.

The [committed results](evidence/capture-results.json) contain permission checks, target hashes, capture metadata, oracle submissions, and separate disclosure and action outcomes. The [representative protected-window capture](evidence/protected-screenkit.png) shows readable HTML while inspection is disabled. Full images, OCR output, and fixture events remain under `artifacts/capture-final/`.

The first capture adapter crashed before producing an image. Initializing AppKit fixed its window-server setup. Absolute evidence paths fixed a separate app-launch working-directory error. Invalid adapter runs remain local and do not count as protection or accepted capture trials.

## Playwright probes

Pinned Playwright Core 1.64.0 connected over CDP to an isolated installed Chrome instance. It recovered the fixture marker and completed all three control tasks. The control used its own temporary profile and did not reuse a personal browser profile.

The native protected build and inspectable control exposed no usable CDP endpoint in the tested launch configuration. Playwright's custom WebKit executable route also failed against both. These failures are recorded as unsupported transports, not defensive blocks. CDP attachment supports Chromium, and Playwright's native WebKit driver expects its patched browser. [Official Playwright connection documentation](https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp).

See [raw transport results](evidence/playwright-results.json). The report preserves errors and the working Chrome control. It does not claim that Playwright cannot contribute to a native computer-use attack.

## Native inspector discovery

Safari's Develop menu listed the inspection-enabled native control and its local fixture. It did not list the running protected browser in the observed target list. A successful end-to-end inspector attachment was not established. Native menu actions returned `Accessibility error: AXError.invalidUIElement` during the attempt.

[Discovery evidence](evidence/inspector-discovery.json) separates the observed target list from unverified attachment. Safari's developer-menu preference was restored to its initial state. No remote-automation option was enabled.

The result is consistent with the configured inspection setting. It does not pass the full protocol and lifecycle gate in the PRD.

## Reproduce

With the current probe grants and fixture server available:

```sh
python3 tools/run_capture.py --repetitions 3 --output artifacts/capture-repeat
npm ci --ignore-scripts
npm run probe:playwright
```

Keep native input trials separate from other desktop interaction. The probe refuses global input when its target is not frontmost. A lost window, missing grant, crash, timeout, or OCR failure is inconclusive for prevention.

This is not an exhaustive attack inventory. Display capture, recording, lifecycle transitions, real human usability, blind keyboard replay, and full Safari inspector attachment remain unvalidated. No physical trajectories were collected. The next bounded experiment tests a source-state filter against generated HID-state events.
