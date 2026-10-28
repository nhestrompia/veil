<img src="assets/icon.svg" width="64" height="64" alt="">

# AgentFreeBrowser

A macOS research browser that tests whether humans can use websites while agents cannot.

In the current browser, a human completed a click task. **Seven generated-input trials caused no new action while the hardware pointer stayed armed.** GPT-6.1-terra completed the readable control. Its candidate trial recorded an extra page click of unresolved origin, so input prevention remains inconclusive. See the [findings](docs/hardware-pointer-findings.md). These results do not prove that every agent or route fails.

The prototype has one window, an address bar, back, forward, and reload. Hardware mouse support is the default. The browser supports this Mac's measured built-in keyboard, US ASCII, and primary webpage clicks through the tested USB mouse. The green ring supplies click positions. Ordinary OS mouse events stay blocked. Hover, drag, scroll, and other mouse features remain unsupported.

## Let an agent test it

Give your agent this command. It launches the **real native browser**, returns its PID, and leaves the agent in control:

```sh
python3 tools/agent_browser.py start \
	--url 'https://en.wikipedia.org/w/index.php?title=Special:Search' \
	--task 'Search Wikipedia for WebKit using this browser.' \
	--agent-label 'MODEL / CLIENT'
```

Tell the agent to read the returned `taskFile` and complete the task with its own Playwright, computer-use, or native tools. No human page-opening step is part of this run. Use any HTTPS URL and website task.

The command launches the mouse-enabled `dist/AgentFreeBrowserPointer.app`. It does not simulate actions, inject input, or enable debugging. If startup navigation is blocked, record that stage. Do not call it a loaded-page test. Use `--target engine` for the frozen keyboard-only comparison. The default change does not resolve the unexplained click or establish an agent-free guarantee.

[Test it yourself](docs/testing-with-agents.md#test-it-yourself) · [Agent-owned testing guide](docs/testing-with-agents.md) · [Model results template](docs/model-test-results.csv)

## Build availability

The installed research app runs on this prepared Mac. It depends on the workspace's custom WebKit engine. A portable release is not available yet. A missing build is a setup failure, not browser protection. See [build status](docs/build-and-distribution.md).

## Results

- [Current mouse tests and evidence](docs/hardware-pointer-findings.md)
- [Earlier keyboard-only tests](docs/focus-engine-live-findings.md)
- [Publication report](docs/publication-report.md)
- [Remaining tests](docs/agent-free-gap-audit.md)
- [Proof-of-concept PRD](PRD.md)

Created in [T3 Code](https://t3.codes).
