# Native host Reload experiment

Three readable references reloaded through external Accessibility actions. The same helper found no address field or Reload button in three matched scans of the restricted browser. It attempted no candidate action. The fixture recorded no new page load or form submission for the candidate.

## Method

RendererAXProbe scanned native host tokens for element IDs 0 through 1,023. Each scan had a three-second limit, followed by an eight-second total query limit. The helper checked the exact executable, process start time, and element owner before reads. It skipped menu contents and installed no input hook.

The Reload action required the exact loopback fixture address and foreground research host. The existing helper also retains a fixture-guarded form branch. No form action ran in these comparisons. The controller requires a successful AX press, one new `page-ready` event, zero accepted form actions, and verified cleanup before it accepts a reference. Lifecycle events support the Reload result but are not authenticated action receipts.

The controller required the unchanged candidate, completed physical baseline, device binding, and desktop input safeguards. Each reference closed before the candidate scan. All helper and reference cleanups passed.

## Results

| Observation | Readable references | Restricted candidate |
| --- | --- | --- |
| Comparisons | 3 | 3 |
| Address field and Reload resolved | 3 | 0 |
| Reload actions sent | 3 | 0 |
| New page-ready events | 3 | 0 |
| Accepted form actions | 0 | 0 |

The candidate remained PID 61893, with executable SHA256 `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`. The helper SHA256 was `82d0c15dadfa49d1669a576270c08cb9b749d6fe102b1724fa61f6dd2d9b08a7`. Accessibility was effective in every run. The user authenticated the approved exact-bundle re-add before testing.

## Limits and next work

The result is controls-not-reachable within a fixed scan budget. It does not establish rejection of a directly addressed action. Candidate form submission was not tested by this route. Other IDs, APIs, builds, and websites remain open. The browser is not proven agent-free.

Repeat calibrated native input and semantic attacks on this exact physical session. Earlier completed native matrices belong to other PIDs. Keep the executable frozen so these results share one identity.

[Saved results](evidence/host-navigation-results.json) contain all three comparisons. Raw files are in `artifacts/host-navigation/live`, `repeat-1`, and `repeat-2`.
