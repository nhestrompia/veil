<img src="assets/icon.svg" width="64" height="64" alt="">

# AgentFreeBrowser

A macOS research browser that tests whether humans can use websites while agents cannot.

In recorded tests, **GPT-6.1-sol did not complete the website task through the tested native input, Accessibility, and focus routes**. A human completed the task twice in the same browser process. These results cover the tested routes and build. Unfiltered display capture and external script attachment remain open tests.

The current prototype has one window, an address bar, back, forward, reload, and keyboard input. It supports this Mac's measured built-in keyboard and US ASCII. Mouse input is disabled.

## Test it

Follow [Test with your agent](docs/testing-with-agents.md). It covers human setup, Google/Wikipedia/GitHub tasks, readable controls, and model comparisons.

On the prepared test Mac, start a Wikipedia session:

```sh
python3 tools/website_challenge.py --target engine --site wikipedia --search-page \
	--agent-label "MODEL / CLIENT" --output artifacts/my-model-wikipedia
```

The command writes `AGENT-TASK.md`, the browser PID and hash, and an attempt template. Use a fresh session for each model.

## Browser download

Compiled apps are **not included in Git**. The current engine app depends on this workspace's custom WebKit build and fixed paths. A portable download is not ready.

For public testing, publish a packaged browser and readable control as release assets, with checksums and test instructions. See [Build and distribution status](docs/build-and-distribution.md).

## Results

- [Current tests and evidence](docs/focus-engine-live-findings.md)
- [Publication report](docs/publication-report.md)
- [Remaining tests](docs/agent-free-gap-audit.md)
- [Proof-of-concept PRD](PRD.md)

Created in [T3 Code](https://t3.codes).
