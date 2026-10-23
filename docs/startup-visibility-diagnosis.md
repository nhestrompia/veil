# Startup visibility diagnosis

The revised keyboard browser failed its physical control. The user reported that the whole window was black. The reader opened and bound a keyboard. Logs recorded five admitted key-down events, but the independent fixture recorded no page events or submissions.

The earlier physical-submit launch test still describes unattended network behavior. It cannot establish usable protection. The [human failure](evidence/startup-human-failure.json) remains part of the evidence.

Two internal controls narrow the diagnosis. A separate native address field handled a constructed Return through both direct application dispatch and the ordinary queue. A diagnostic copy of the full browser also handled an internally authorized Return and loaded the fresh loopback endpoint. Neither control opened a device reader.

The [native field control](evidence/native-address-dispatch-control.json) and [full startup control](evidence/startup-internal-control.json) do not reproduce the user's visibility failure. They do not prove that physical input or the real display works. The full diagnostic copy is a modified test binary, not an external agent bypass.

The next comparison changes only the sharing restriction. The `devicekeyboard-visible` build replaces the same research app with sharing enabled. It keeps the event gate, pending-address workflow, and Accessibility overrides. It uses the same separately approved Input Monitoring recipient. The revised ad hoc signature needs that existing registration refreshed.

The two build flavors are mutually exclusive at the same app path. They are not separate simultaneous browsers. A visible control necessarily exposes the fake page to capture, so it cannot establish the agent-free goal. Its purpose is to distinguish window visibility from startup input.

```sh
bash scripts/build.sh devicekeyboard-visible
bash scripts/diagnose-address-dispatch.sh
bash scripts/diagnose-startup-address.sh
```

The isolated controls run only their own fake native field or a disposable loopback page. Debug instrumentation stays in the generated diagnostic copy under the ignored build directory. The production browser contains no internal test-event command.


The unprotected window capture showed its address bar and startup instructions. The operator still reported a black whole window. A later process check found the research app hidden and inactive. Activation changed its state to active and unhidden. One built-in main display covered the window's recorded bounds. No other research process was running.

This evidence does not prove why the app became hidden. It also does not establish which window the operator viewed. The user then selected the app with Command-Tab and confirmed that the address bar was visible. This confirms visibility after explicit selection. It does not confirm navigation or explain the earlier hidden state. The earlier failure and the capture remain separate observations.


A fresh physical session exposed another startup problem. The user reported that Space replaced the address. The log recorded an existing device binding and later admitted events. The first binding key was already consumed. Later Spaces reached the selected address field as ordinary typing. An isolated native-field control reproduced this exact replacement.

The revised dispatcher consumes repeated Spaces until the first valid navigation starts. A binding callback selects the address and shows a ready message. After navigation begins, Space works normally. The native control failed before the change and passed afterward. It also verified Return submission and normal Space input after navigation. These internal events establish the regression result, not physical provenance.

The [startup regression](evidence/startup-space-regression.json) records both results. The latest [launch comparison](evidence/launch-space-fixed.json) recorded zero unattended requests in three candidate trials, with three working controls. A new physical task and attacks against that same process remain required.


The revised visible control subsequently passed physical website completion. Expanded attacks against that same process refused 27 calibrated native trials and three vision-input trials. Six native trials remained inconclusive. Screenshots disclosed the page. See the [same-session results](device-startup-session-findings.md).
