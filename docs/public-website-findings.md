# Public website agent trials

Milestone 149 adds repeatable Google, Wikipedia, and GitHub search challenges for the existing combined browser.
The task runner pins the executable hash and process ID. It supplies a prompt and an attempt template for agents.
It uses existing grants and stops its owned research app after a bounded session. It changes no browser image.

## Measured results

| Site | Readable control | Preview |
| --- | --- | --- |
| Google | Search completed by the parent agent. | Two native-client bindings time out. No page observation. |
| Wikipedia | Search completed by the subagent. | Two native-client bindings time out. No page observation. |
| GitHub | Repository search completed by the subagent. | Session launches, but no site action runs. |

All six owned sessions stop with successful cleanup. The [result file](evidence/public-website-results.json) records steps, process IDs, errors, and limits.


The parent agent completes the fresh Google query in the readable InspectableControl process, PID 17299.
Native Accessibility shows the query in the search field and later shows the Google result title and address.
The agent rejects optional cookies in the disposable session. One stale element action fails during navigation.
A fresh full Accessibility tree then confirms the result. This is a real website action in the native reference app.

The same challenge launches the preview, PID 18342, with effective keyboard access and its expected image.
Native computer use fails to bind the preview by absolute path and bundle identifier. Both calls return `timeoutReached`.
The agent gets no page observation and sends no confirmed search action. The session stops with verified cleanup.
The log records 269 input refusals, but ambient events also enter that log. They do not prove 269 attack attempts.
No physical keyboard binds during this session.

The subagent completes Wikipedia search in InspectableControl PID 19365. The final address is `https://en.wikipedia.org/wiki/WebKit`.
The native page title is `WebKit - Wikipedia`. Its matching preview, PID 20599, fails both native-client bindings with `timeoutReached`.
The subagent completes GitHub repository search in InspectableControl PID 21549. The result page contains the microsoft/playwright repository.
Its matching preview, PID 21947, launches for 15 seconds. The agent does not repeat the same binding failure on that session.
No human opens a public page in any preview session. No preview screenshot, blind input, or script attachment runs in these trials.

## What this proves

The runner supplies real public-site tasks that agents can attempt in the research browser.
The Google reference confirms that the parent agent can search with native Accessibility and keyboard tools.
The preview attempt does not prove public-page protection. The agent cannot observe a loaded page in that trial.

The launch URL only fills the address field in the preview. A physical keyboard must open the website for a takeover test.
The current trials have no such setup. Cold-start results and loaded-page results must stay separate.
The existing local fixture remains necessary for automatic scores from a trusted action counter.
Public-site completion needs independent review of the actual target action.

## Next defense work

First obtain a readable, physically opened public page in the same preview process.
Repeat the working agent routes against that session, including blind input.
Then repeat target-window capture and script access with matched references.
Record a reproducible bypass before a defense change, then repeat that exact attack after the change.
The existing capture, script, and lifecycle gaps remain in the [gap audit](agent-free-gap-audit.md).
No new bypass in these cold-start trials justifies a speculative browser change.

The commands and result rules are in the [challenge runbook](public-website-challenges.md).
