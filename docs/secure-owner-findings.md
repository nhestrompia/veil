# Direct Secure Input ownership comparison

Milestone 65 checks the installed WebKit's private per-view bookkeeping flag. A diagnostic calls only `_secureEventInputEnabledForTesting` on its own WKWebView. It checks the Objective-C signature before the read. It does not enable or reset Secure Input.

One fresh ordinary comparison and one fresh stable-host comparison used password fields. Both passed readable references and private keyboard baselines. The external cycle only hid, restored, and activated research apps. It posted no input and made no Accessibility call during the cycle.

| Observation | Ordinary host | Stable host |
| --- | --- | --- |
| WebKit ownership while hidden | false | true |
| Aggregate Secure Input while hidden | false | true |
| Another research app foreground after settling | yes | yes |
| New external focus actions | 1 | 0 |
| New private resumed tasks | 1 | 1 |
| Temporary cleanup | passed | passed |
| Aggregate Secure Input after cleanup | false | false |

The stable host retains its own bookkeeping flag while hidden and another research app is foreground. This directly strengthens the earlier ownership inference. The ordinary host releases that flag. Its focus-only website bypass also reproduces.

Every logged resumed private key had ownership and aggregate protection enabled. These samples use generated private input. They do not establish physical-password protection, OS call success, or protection across every navigation and editor transition.

The default diagnostic was restored without logical host getters or ownership logging. Frozen physical browser and probe binaries remain unchanged. The engine projection still requires a build and live comparisons. Its native window state remains actual.

Pinned source inventory: [full audit](research/activity-full-source-audit.md). Saved results: [ownership evidence](evidence/secure-owner-results.json).
