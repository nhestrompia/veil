<img src="assets/icon.svg" width="64" height="64" alt="">

# AgentFreeBrowser

A macOS research browser that tests whether humans can use websites while agents cannot.

In recorded tests, **GPT-6.1-sol did not complete the website task through the tested native input, Accessibility, and focus routes**. A human completed the task twice in the same browser process. These results cover the tested routes and build. Unfiltered display capture and external script attachment remain open tests.

The current prototype has one window, an address bar, back, forward, reload, and keyboard input. It supports this Mac's measured built-in keyboard and US ASCII. Mouse input is disabled.

## Let an agent test it

Give your agent this command. It launches the **real native browser**, returns its PID, and leaves the agent in control:

```sh
python3 tools/agent_browser.py start \
	--url 'https://en.wikipedia.org/w/index.php?title=Special:Search' \
	--task 'Search Wikipedia for WebKit using this browser.' \
	--agent-label 'MODEL / CLIENT'
```

Tell the agent to read the returned `taskFile` and complete the task with its own Playwright, computer-use, or native tools. No human page-opening step is part of this run. Use any HTTPS URL and website task.

The command launches `dist/AgentFreeBrowserEngine.app`. It does not simulate actions, inject input, or enable debugging. If the app blocks navigation at startup, record that stage. Do not call it a loaded-page test.

[Agent-owned testing guide](docs/testing-with-agents.md) · [Model results template](docs/model-test-results.csv)

## Build availability

The installed research app runs on this prepared Mac. It depends on the workspace's custom WebKit engine. A portable release is not available yet. A missing build is a setup failure, not browser protection. See [build status](docs/build-and-distribution.md).

## Results

- [Current tests and evidence](docs/focus-engine-live-findings.md)
- [Publication report](docs/publication-report.md)
- [Remaining tests](docs/agent-free-gap-audit.md)
- [Proof-of-concept PRD](PRD.md)

Created in [T3 Code](https://t3.codes).
