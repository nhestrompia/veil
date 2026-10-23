<img src="assets/icon.svg" width="64" height="64" alt="">

# agentfreebrowser

A macOS-only research project for an agent-resistant browser, with agent-free browsing as the stronger research goal.

Start with the [proof-of-concept PRD](PRD.md). It defines the target, proposed architecture, MVP requirements, attack tests, and acceptance gates.

Supporting evidence:

- [Antiagent review](docs/research/antiagent-review.md): what worked, what failed, and which test methods to reuse.
- [Browser feasibility research](docs/research/browser-feasibility.md): official sources for inspection, accessibility, screen capture, native input, and session handling.
- [Mouse-behavior experiment](docs/research/mouse-behavior-experiment.md): physical trajectories, human-trace replay, adaptive attacks, and false blocks.
- [Protected-rendering experiment](docs/research/protected-rendering-experiment.md): a separate track for interactive HTML and capture-protected graphics paths.

The proposed starting point is AppKit and WKWebView. No browser implementation exists yet. Start with 2 to 3 days of experiments, with native input first. A resistant MVP needs measured benefits and explicit limits. The stronger agent-free claim requires separate prevention results for accessibility, capture, and native input.

The local Antiagent review checks saved evidence. The online report reviews primary sources. Neither constitutes a live test of this proposed browser.

Created in [T3 Code](https://t3.codes).
