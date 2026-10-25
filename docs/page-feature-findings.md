# Cross-page tests and an external focus bypass

An external agent completed a new website action by activating the research browser. Three fresh candidate processes each recorded one new accepted action. The agent posted no keyboard or mouse input and made no Accessibility call during the activation cycle. The input gate admitted zero events. This defeats the broad all-pages action claim for this prototype.

## Focus-only action

The new fixture keeps an ordinary form. After its first accepted task, it records another action when its window receives focus. This is ordinary page JavaScript. It uses no injected browser bridge or private app state.

The candidate first completed one private authorized keyboard task. That diagnostic uses the same application gate and protected WebKit configuration, with a private input source and focus assistance. It does not start the hardware reader. It is not a physical-human control.

The attacker activated a separate research window, then activated the candidate. The standalone ResearchFocus helper used only NSRunningApplication.activate and checked the foreground PID. Each readable reference and candidate recorded one new accepted action on return. All three candidate logs recorded zero accepted input events during that cycle. No AX read, value mutation, or press occurred in the candidate cycle.

An earlier three-run comparison used activation inside the existing AX-read probe. It also completed the action. The standalone comparison removes that extra AX access and reproduces the result. All reference, sink, and candidate processes passed cleanup.

## Other page features

The initial matrix covered ordinary inputs, textareas, editable regions, open and closed shadow DOM, dynamic rendering, same-origin frames, cross-origin frames, and srcdoc. Seven modes completed their private baseline. Their 35 external cases produced 21 explicit native blocks and 14 inconclusive results. No new task completed through those tested typing, click, vision, or AX routes.

| Page feature | Initial private task | Follow-up |
| --- | --- | --- |
| Ordinary input | Passed | Three native routes blocked |
| Editable region | Passed | Three native routes blocked |
| Open and closed shadow DOM | Passed | Three native routes blocked for each mode |
| Dynamic rendering | Passed | Three native routes blocked |
| Same-origin and cross-origin frames | Passed | Three native routes blocked for each mode |
| Textarea | Failed | A fresh unchanged-build retry passed and blocked its matched HID attempt. Cause of the first failure remains unknown |
| Srcdoc | Failed | No attack ran. The current navigation policy rejects its about URL |

Vision observations found no usable target field, so they do not establish input prevention. Candidate AX targets were unavailable. The textarea AX reference also failed. These cases remain visible as inconclusive.

## Controller correction

The first input matrix measured submissions around each input call. The focus result showed that actions can occur earlier, during foreground preparation. The revised controller measures those transitions too. It counts a new accepted action even if the intended reference adapter fails. The focus fixture now belongs to the default suite. Its regression run reports a bypass before posting input.

Trial IDs and failed oracle snapshots now persist when readiness fails. The new server runs on loopback port 8766 with a separate controller file. The original fixture and physical PID 61893 remain unchanged. No permission changed and no global input hook was installed.

## Consequence and next experiment

Blocking synthetic NSEvents does not cover all browser state changes. This result concerns a diagnostic process with the real shared gate and configuration. The frozen physical browser did not load this new page, so its exploitability remains untested.

Next, test whether the browser can hold WebKit focus state steady across external activation while preserving authorized typing. Do not count a black, noninteractive, or baseline-failing window as a fix. Generic web compatibility and agent-free status remain unmet.

[Saved evidence](evidence/page-feature-results.json) retains the full matrix, failed baselines, both focus comparisons, the regression, and cleanup. All 85 Python checks pass.
