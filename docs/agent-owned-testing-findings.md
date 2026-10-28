# Agent-owned browser launcher verification

The default workflow now lets an agent start, inspect, and stop the actual native browser. It accepts a website URL and task. It supplies no scripted website actions, input injection, diagnostic bootstrap, or automation endpoint.

The agent receives the exact app path, executable, bundle ID, PID, image hash, task file, and session file. Generated tasks prohibit requests for human navigation, input, and runtime verification. Agent-only mode is the default. Human-assisted takeover research requires an explicit mode.

## Live checks

The start command opens AgentFreeBrowserEngine PID 40434 with its unchanged image, SHA-256 `12de797fbbfea6f5536b13b8ba890354170f3561f681620bb49be42f2fdf7e21`. Status confirms that this process runs. A normal macOS URL-open attempt reaches the browser, which logs its external-open refusal. The app remains at its address-entry policy. No website navigation or loaded-page operation is established in this check.

The stop command closes that owned app and records successful cleanup. No engine process remains after the test. No human setup, permission change, utility pause, administrator access, or input hook occurs.

Two readable-control checks use the same saved website task. The first AX read happens before the page loads and returns an empty web area. That is not a positive page control. A later fresh session waits for network loading. The native tool then reads the actual web-area description, Search - Wikipedia. Both control sessions stop successfully without human input.

These checks verify the launcher and real app lifecycle. They do not establish an agent-free browser or a completed website task. A model still needs to use its own tools, record each stage, and preserve partial actions or blocked startup.

Forty-five relevant Python tests pass. Tests cover agent-only worker launch, custom-task validation, default prompts without human setup, startup metadata without a page-load claim, cleanup, and refusal of changed identities. The browser binary and existing permission grants remain unchanged. See [saved verification](evidence/agent-owned-browser-verification.json) and [the test guide](testing-with-agents.md).
