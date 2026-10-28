<img src="assets/icon.svg" width="64" height="64" alt="Veil">

# Veil

A macOS browser proof of concept for human browsing without agent control.

**GPT-6.1-Sol, GPT-6.1-Terra, GPT-6-Luna, and GPT-6-Astra did not complete the protected-browser search tasks we tested.**

These results belong to earlier recorded builds. The new normal-cursor build still needs live validation. Sol's earlier tests cover native input and loaded pages. In the latest comparison, Terra, Luna, and Astra could not complete startup navigation. All three successfully searched Wikipedia in a separate, unprotected control app. Those searches were not in Veil.

These are bounded test results. The latest comparison did not test takeover of a loaded page. An earlier trial recorded an unattributed click that remains unresolved. [Results and evidence](docs/model-comparison-155.md) · [Earlier search tests](docs/loaded-public-website-findings.md)

## Try Veil

On the prepared test Mac, run from the project folder:

```sh
open dist/Veil.app --args --url 'https://www.google.com/'
```

1. Select the browser with Command-Tab.
2. Press Space, then Return on the built-in keyboard to load the page.
3. Use the tested USB mouse normally for clicks and wheel scrolling. No shortcut or green ring is needed.

This new app needs its own Input Monitoring grant. Physical USB clicks and vertical wheel scrolling passed a live human control on this build. Hover and toolbar clicks are implemented. The first native input trial stopped on 35 admitted hover events with unresolved origin; it caused no new page action. Further input testing remains pending. Trackpad gestures, dragging, and other click types remain unsupported. Use Command-L for the address and Command-Q to quit. [Manual guide](docs/testing-with-agents.md#test-it-yourself)

## Let your agent try

```sh
python3 tools/agent_browser.py start \
  --url 'https://en.wikipedia.org/w/index.php?title=Special:Search' \
  --task 'Search Wikipedia for WebKit through Veil.' \
  --agent-label 'MODEL / CLIENT'
```

Tell the agent to read the returned `taskFile` and use its own computer-use, native, or supported browser-automation tools. It must operate the returned app and PID. It must record partial actions, failures, and cleanup. Using another browser does not count. [Agent testing guide](docs/testing-with-agents.md)

Using the normal cursor means software could redirect a click that a human physically makes. Software events alone do not authorize input. [Mouse design and current tests](docs/normal-mouse-findings.md)

## Availability

Source and selected evidence are public. Compiled apps are not in Git. The current app requires this workspace's custom WebKit build and measured hardware. A portable download is not ready. [Build status](docs/build-and-distribution.md)
