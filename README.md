<img src="assets/icon.svg" width="64" height="64" alt="">

# agentfreebrowser

A macOS-only research project for an agent-resistant browser, with agent-free browsing as the stronger research goal.

Start with the [proof-of-concept PRD](PRD.md). It defines the target, proposed architecture, MVP requirements, attack tests, and acceptance gates.

Supporting evidence:

- [Antiagent review](docs/research/antiagent-review.md): what worked, what failed, and which test methods to reuse.
- [Browser feasibility research](docs/research/browser-feasibility.md): official sources for inspection, accessibility, screen capture, native input, and session handling.
- [Mouse-behavior experiment](docs/research/mouse-behavior-experiment.md): physical trajectories, human-trace replay, adaptive attacks, and false blocks.
- [Protected-rendering experiment](docs/research/protected-rendering-experiment.md): a separate track for interactive HTML and capture-protected graphics paths.

The initial AppKit and WKWebView shell is implemented. See [implementation milestones](docs/implementation.md) for build commands and verification. The first experiments test native input. A resistant MVP needs measured benefits and explicit limits. The stronger agent-free claim requires separate prevention results for accessibility, capture, and native input.

The local Antiagent review checks saved evidence. The online report reviews primary sources. Neither constitutes a live test of this proposed browser.

Live prototype results:

- [Native input](docs/native-input-findings.md): five working CGEvent adapters completed all 15 protected-browser trials.
- [Capture and automation](docs/capture-findings.md): screenshot/OCR/native input completed 3/3 protected-browser trials. Playwright transport failures remain separate from protection evidence.

Created in [T3 Code](https://t3.codes).
