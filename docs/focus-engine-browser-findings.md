# Integrated engine policy for focus actions

Milestone 152 implements a focus defense in a separate browser candidate. Six matched diagnostic comparisons pass. Stable mode records no new website action across 18 activation cycles, while native mode reproduces actions in every case. Each resumed typing control completes. Milestone 153 adds a physical text control and live focus repeat on the public app. See the [live findings](focus-engine-live-findings.md).

The frozen preview remains vulnerable as measured in [milestone 151](preview-focus-action-findings.md). Its executable stays unchanged. The new app is `dist/AgentFreeBrowserEngine.app`, with bundle identifier `research.agentfreebrowser.focusengine`. The [manifest](evidence/focus-engine-browser-manifest.json) pins its executable, engine dependencies, and source files.

## The engine separates page activity from native focus

The new target enables the existing WebKit research policy before constructing the web view. It checks the effective configuration after WebKit copies it. The engine projects active, focused, visible, visible-or-occluded, and in-window flags when it sends activity to content processes. It also clears visual idle in that content projection.

Native AppKit state remains real. The keyboard router still requires the actual key window and foreground process. WebKit's native password-input ownership code remains separate from projected page activity. No JavaScript event handler is removed or replaced, and no native window getter pretends the window is active.

The app checks fixed engine paths and compiled image hashes. It checks UI framework origins before page creation and content executable identity at commit and completion. The fixture runner independently verifies mapped WebKit, WebCore, and JavaScriptCore images in each initial measured main content process. These are runtime checks, not proof of a barrier before all renderer execution.

## Matched results

The complete serial suite uses the same combined browser controller in two diagnostic apps. One selects native activity and the other selects stable activity. Their private owner-generated input arms a loopback fixture and tests resumed typing. That input is a routing control and does not establish physical-human operation.

| Case | Native actions across three cycles | Stable actions across three cycles | Resumed task |
| --- | --- | --- | --- |
| Ordinary focus | Three | Zero | Passed in both modes |
| Password focus | Three | Zero | Passed in both modes |
| Window blur | Three | Zero | Passed in both modes |
| Hide and restore visibility | Six | Zero | Passed in both modes |
| Same-origin frame focus | Three | Zero | Passed in both modes |
| Cross-origin frame focus | Three | Zero | Passed in both modes |

Each activation interval has zero admitted input. Each one-second stationary control has zero new actions. The external actor only activates, hides, or unhides exact pinned research apps. It sends no keyboard, mouse, Accessibility action, or action request.

The password case records its view's Secure Event Input ownership as false while another app is foreground and true after return. Aggregate Secure Event Input follows those states in the recorded samples. The resumed password task completes. Dynamic background editor changes and physical password typing remain separate validation work.

An additional stable focus cycle after reload records no action. A second resume command completes one task. Sequence IDs ensure repeated commands work. This is a reload test, not forced renderer-crash recovery.

The [result file](evidence/focus-engine-browser-results.json) contains the full suite, earlier inconclusive attempts, startup checks, hashes, and cleanup. All 43 relevant Python tests pass. The default target also passes its exact-event checks and 14 navigation checks. All 14 recorded frozen research executable hashes remain unchanged.

## Failed controls remain in the record

The first focus comparison fails its scoped activation helper and does not run a stable candidate. The helper now uses kernel process-start identity for CLI-launched research apps. An early password run ends before its third cycle completes. Its two completed cycles are observations, not a full pass. The final diagnostic has a longer bounded lifetime and explicit timeout logging.

The first visibility control reports a false API return despite reaching hidden state. The runner now keeps that raw return value and separately requires the measured end state. API success cannot replace a missing state change. The repaired control and subsequent complete suite pass. None of the earlier failures counts as browser protection.

## Packaging and acceptance limits

The new app can start through its native bootstrap, which restarts the same executable with the fixed research engine. A wrong engine root is refused. The engine still lives in this workspace. It is not bundled for distribution, and this candidate is ad hoc signed without Hardened Runtime. Those are material limits. Earlier capture, script, and input resistance results cannot transfer automatically to this new build.

Milestone 153 obtains the approved Input Monitoring grant and confirms effective access through native app launch. Both the launcher and the app require the approved manifest record before a request. These approval checks control the research workflow. They do not create an OS permission boundary. The exact shipping executable has no diagnostic typing driver or fixture command channel.

Physical text use and the external focus repeat pass in milestone 153. Physical password use remains required. The prepared session runner supports `--engine`, and the separate [attack runner](../tools/run_focus_browser_attack.py) requires that exact physical declaration and a successful native-engine reference.

This milestone implements the engine fix and validates diagnostic behavior. It does not certify the public app as agent-free. Unfiltered capture, external inspector scripting, physical compatibility, renderer recovery, and other OS-driven actions remain unresolved.
