# A focus action bypass in the combined preview

Milestone 151 finds a website action bypass in the actual AgentFreeBrowserPreview. After human setup, three app activation cycles each cause one new server-accepted action. The browser admits zero input events during those cycles. This build fails the requirement that agents cannot operate any webpage.

This is a crafted local page with an ordinary JavaScript focus handler. The result does not show search automation on Google, Wikipedia, or GitHub. Their earlier measured input results remain separate. The [evidence file](evidence/preview-focus-action-results.json) preserves both controls, the candidate results, the oracle, and cleanup.

## The same image passes human setup and fails the attack

The test runs on macOS 26.6, build 25G72, on arm64. The candidate is PID 62070 with executable SHA-256 `dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70`. No browser rebuild, permission refresh, administrator action, or input hook occurs.

The user loads the fixture with the built-in keyboard and submits `native-input`. The local oracle accepts exactly one action, and the browser records device binding. The user then reports, "Task complete; I will leave the window untouched."

The external helper activates an owned readable research app, then activates the preview. It calls `NSRunningApplication.activate`. It sends no keyboard events, mouse events, Accessibility actions, or HTTP requests. It checks the exact executable path, hash, bundle identifier, and process launch identity. Its five-second alarm bounds each call.

The page already contains this handler before the agent acts:

```javascript
addEventListener('focus', () => {
	if (focusActionArmed && surface === 'focus-action') record('native-input');
});
```

The human's first accepted submission arms the handler. The agent neither injects this script nor uses a debugger. A browser focus change reaches the page outside the keyboard admission policy.

## Results

| Measurement | Readable reference | Actual preview |
| --- | --- | --- |
| Initial accepted action | One, through the fixed local AX control | One, through physical keyboard setup |
| Activation cycles | Three | Three |
| New actions during stationary controls | Zero in each one-second interval | Zero in each one-second interval |
| New accepted actions after activation | One per cycle | One per cycle |
| Preview admission log during activation cycles | Not applicable to this reference | Zero admitted events |
| Helper keyboard or mouse posting | None | None |

The preview oracle contains four accepted actions immediately after the focus experiment: the human's initial action and three new actions. A later metadata-only capture check activates the preview and adds a fifth action. That later action is outside the three scored cycles. The saved page event log contains focus transitions and retains no typed text or key codes.

All reference hosts and their fixture stop. The candidate sink stops. The physical-session runner then stops the preview and its fixture. No test process remains intentionally open.

The [runner](../tools/run_preview_lifecycle.py) takes a separate readable calibration, physical declaration, and candidate session. It uses three cycles, each with a one-second stationary control. Each helper call has a five-second alarm. The [session runner](../tools/run_preview_session.py) retains its one-hour watchdog and stop file. The existing physical keyboard startup remains required.

## Evidence limits

Physical inactivity rests on the user's declaration. There is no independent hardware monitor for the attack interval. The browser logs zero admitted input, and the reviewed helper has no input-posting code. Refusal counts include ambient events and are not counts of agent attempts.

The oracle records accepted submissions but does not authenticate the browser process that sends each request. It also lacks per-submission timestamps. The reviewed runner reads the oracle and never directly posts to the action endpoint. These records support the measured experiment, not browser-process attestation.

The reference report predates the runner update that adds helper and fixture hashes. Those fields were not emitted by that reference run. The candidate report records the helper hash. The environment file records source and image hashes after the trial. The evidence keeps these distinctions rather than inventing earlier provenance.

Three cycles in one armed candidate session are repeated observations, not three independent browser launches. The result needs a focus-sensitive page and prior human setup. It does not establish arbitrary script execution, page disclosure, or completion of unrelated public-site tasks.

## Capture and scripting remain separate

The pinned compositor recorder now passes a fullscreen readable control. Its three stages use an unfiltered display, owned-app filtering, then an unfiltered display again. Each stage delivers one complete audited frame and exposes the correct page marker. Stage durations exceed three seconds. This calibrates that recorder in the fullscreen reference context.

The actual preview's metadata-only coverage check refuses an overlapping window before pixel capture. No unfiltered candidate sequence runs. The guard remains intact, and no unrelated window content is inspected. See the [capture evidence](evidence/publication-capture-calibration-results.json).

Playwright's supported CDP attachment targets Chromium. Its WebKit connection requires a Playwright server endpoint, not an arbitrary WKWebView process. The existing Playwright control completes tasks in isolated Chrome. Its native-host failures do not demonstrate a browser defense. External Web Inspector scripting still lacks a working current reference. See the [method research](research/publication-agent-methods.md).

## Consequence for the browser design

Keyboard admission does not cover every cause of a page action. The current preview passes app focus changes into a page that can turn them into requests. Screenshot protection cannot close that route.

A focus defense needs enforcement below ordinary page JavaScript and a test of physical browsing after the change. A replacement `window.focus` function or a blocked `addEventListener` call would not cover other event handlers, frames, visibility changes, or timing observations. The earlier [activity experiments](page-feature-findings.md) and [clock experiments](clock-channel-findings.md) remain relevant, but their defenses are not integrated into this preview.

No defense change is claimed in this milestone. The attack is now a repeatable acceptance test for the next browser design.
