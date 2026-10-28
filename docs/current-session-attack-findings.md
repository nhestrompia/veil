# External actions in the current physical session

Twenty-nine native attempts received explicit input refusals. No input event entered the page, and no new website action completed. Twenty-two additional cases remain inconclusive. Three calibrated semantic comparisons exposed no candidate fixture controls and sent no field write or button press.

These results concern PID 61893, which the user previously operated with the physical built-in keyboard. Earlier native matrices belong to other processes. This experiment does not reuse their outcomes.

## Native input results

The completed matrix and its follow-up contain 51 cases. Each candidate attempt required a fresh reference completion with the frozen NativeProbe. Twenty-one cases skipped candidate input because their references failed. One candidate adapter refused its target lookup. None of these twenty-two cases counts as blocked.

The gate recorded 1,102 refusals across the completed comparisons. The independent fixture still has exactly one accepted task: the earlier physical baseline. The controller did not verify physical input absence during the attacks.

| Native route | Blocked attempts | Inconclusive cases |
| --- | --- | --- |
| `session` | 3 | 0 |
| `hid` | 3 | 0 |
| `private` | 3 | 0 |
| `pid-hid` | 0 | 6 |
| `curve-hid` | 3 | 0 |
| `keycodes-hid` | 3 | 0 |
| `iohid-legacy` | 4 | 2 |
| `iohid-reports` | 4 | 2 |
| `pid-keys-hid` | 3 | 3 |
| `pid-keys-keycodes-hid` | 3 | 3 |
| `pid-window-keycodes-hid` | 0 | 6 |

The counts include repeated cases from the follow-up. They are individual trials, not separate browser sessions. PID-directed mouse controls still failed after foreground activation. Other transient reference and target failures remain in the evidence.

## Foreground setup repair

An initial run could not resolve the candidate's on-screen geometry after reference cleanup. It sent no candidate input. The exact controller received SIGINT, and its cleanup handlers closed its reference. The saved interruption receipt records this failed setup separately.

An exact-target `ax-direct` query activates the research app and checks foreground ownership. After this step, the window appeared at the expected size. The controller now applies this step to both references and candidate before geometry and input. It translates the reference point only between equal-sized windows. It stops on missing candidate geometry, accepted input, or task completion.

The first complete pass recorded eighteen blocks and fifteen skipped cases. The follow-up retried the six affected route families with explicit reference activation. It recorded eleven more blocks, six skips, and one target-lookup failure. No failed reference permits candidate input.

## Native semantics

All three new readable references recovered their markers through tree and focused queries. Each exposed content menus, completed the fixture action, and passed cleanup. Three matched candidate comparisons recovered no marker. Their action adapters found no field or button and sent no action. This establishes unavailable targets through these APIs; it does not establish rejection of a directly addressed action.

## Identities, cleanup, and limits

The browser SHA256 remained `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`. NativeProbe remained `7c256598528dcaf2dcdc6437af30dab92d9c4ca929a55a3a2402f09754f67de1`. No browser or probe rebuild occurred. No permission change was needed.

All reference cleanups passed. Final checks found no temporary reference or probe process. The research browser and fixture remain running. All eighty Python checks pass, including failed-reference, cleanup, posting-error, partial-input, and geometry checks.

The result covers one process, local fixture, measured built-in keyboard, and these adapters. Pointer use and broader website compatibility remain open. Unfiltered capture on this physical build, direct inspector attachment beyond discovery, exports, and session reuse remain open. The browser is not proven agent-free.

[Saved results](evidence/current-session-attack-results.json) retain both complete runs, semantic comparisons, the interrupted setup receipt, and final identities. Raw files are under the directories named in that evidence.
