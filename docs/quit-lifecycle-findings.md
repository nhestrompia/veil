# Graceful-quit lifecycle controls

The fixture now supports armed pagehide and unload beacon actions. The helper checks both the bundle identifier and executable path. Its allowed targets are InspectableControl and InternalKeyboardControl.

One readable comparison per event requested a graceful quit. Both reference apps terminated, but neither fixture recorded a new action. The candidate comparisons were skipped. These results are inconclusive and do not establish browser protection.

Both references passed cleanup. Aggregate Secure Input was off afterward. The helper compiles in Swift 6 with warnings as errors. Pure scope tests allow the two exact disposable paths and reject the physical-browser identity and mismatched paths. Those tests call no process API. All 102 Python checks pass.

Automatic approval review rejected an optional live refusal check against the frozen physical browser. A faulty guard could have closed it. That call did not run. Pure scope tests replaced it. No permission request is pending for the required research work.

A third readable pagehide run checked the rebuilt helper with the extracted scope predicate. It also terminated only its disposable reference and recorded no beacon action. See [saved evidence](evidence/quit-lifecycle-results.json).

Rebuild the helper before these tests:

```sh
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -module-cache-path .build/module-cache Sources/Diagnostics/ResearchQuitScope.swift Sources/Diagnostics/ResearchQuit.swift -o .build/research-quit
python3 tools/run_quit_attack.py --output artifacts/new-quit-run
```
