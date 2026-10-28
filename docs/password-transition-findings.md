# Focused password-transition findings

Milestone 91 reproduces delayed native protection during focused field-type changes. Two fresh native/stable comparisons each complete five private diagnostic tasks. All four processes show the same immediate-transition pattern. The activity projection neither creates nor repairs that pattern in this experiment.

The page starts with an ordinary input. The private diagnostic changes the same focused field through four phases. It types only the fixed fake phrase after each change. The settled phases wait 300 milliseconds. The immediate phases add no wait after the JavaScript completion callback. No external program types into the browser during these controls.

| Phase | First per-view owner flag | First aggregate flag | Later key flags |
| --- | --- | --- | --- |
| Password, settled | true | true | true |
| Text, settled | false | false | false |
| Password, immediate | false | false | true |
| Text, immediate | true | true | false |

Every phase routes thirteen private keys and twenty-six down/up events. Each process completes one startup task and four transition tasks. The field remains focused after its type changes. The first immediate password key precedes the native protection update. The first immediate text key precedes its release. Both flags match the new type before the next key, fifty milliseconds later.

The per-view value comes from the research view's own testing getter. The aggregate value comes from `IsSecureEventInputEnabled`. These snapshots do not prove that an external observer recovered a key. They also do not establish an autonomous input bypass. The saved evidence keeps this result separate from the confirmed process-pause website actions.

The pinned WebKit implementation updates Secure Event Input from the UI process's cached editor state. Its `updateSecureInputState` checks the actual key window and focus, then reads `isInPasswordField`. This explains a possible ordering gap while new editor state travels from the page. The measured flag sequence supports that inference. [Pinned WebKit source](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/mac/WebViewImpl.mm).

All UI and content framework identities passed. Every temporary process passed cleanup, and aggregate Secure Event Input returned to off. All 123 Python checks pass. No frozen browser or permissioned probe changed. [Evidence](evidence/password-transition-results.json) contains both comparisons and the per-key flag arrays parsed from the saved logs.

Reproduce with `python3 tools/run_password_transitions.py --output artifacts/new-password-transition`. Use a fresh output path. The script builds only isolated diagnostics and uses the existing feature fixture.

The next bounded defense is a foreground owner independent of field type. It must balance its own enable/disable calls, use actual native focus, refuse private input without ownership, and release on hide, focus loss, close, or termination. It remains experimental. Retained protection in another app would fail the control. Neither that defense nor this finding resolves the open process-signal route or proves keyboard confidentiality against permissioned observers.
