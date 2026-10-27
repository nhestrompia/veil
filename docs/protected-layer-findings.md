# Standalone protected media comparison

Milestone 124 isolates protected output in one ordinary AppKit window. It displays a clear reference and a protected trial, each with a different marker and color bars. The app contains no WebView, network code, input observer, or permission request.

Both hosted modes fail physical protected visibility:

| Mode | Physical clear panel | Physical protected panel | Marker in window capture |
| --- | --- | --- | --- |
| Hosted H.264 | Text and colors visible | Black | Clear recovered, protected absent |
| Hosted uncompressed NV12 | Visible | Black | Clear recovered, protected absent |

The user reports these results before each screenshot runs. Both panels report ready=true, renderer status 1, advancing sample counts, nonzero bounds, and no errors. These flags therefore do not establish readable physical output.

The hosted configuration assigns AVSampleBufferDisplayLayer as each view's root layer before setting wantsLayer. Apple's [NSView documentation](https://developer.apple.com/documentation/appkit/nsview/wantslayer) specifies this order. Direct layer hosting does not restore protected output in this comparison. Removing H.264 encoding also does not restore it. This does not identify the underlying platform cause or rule out every other rendering design.

The app offers two sublayer modes for later comparisons. Those modes did not run in this milestone. The tests do not establish that compression is necessary for capture exclusion. Neither tested protected mode meets the physical usability requirement.

The first hosted H.264 window expires before the user sees it. Its absent process contributes no physical result. A fresh unchanged launch supplies the actual H.264 observation. That launch and the NV12 launch stop after their completed observations. All three diagnostic hosts are absent.

The app has a ten-minute termination task and an eleven-minute native alarm. Its controller checks the app path and executable hash before stopping its own host. Private state contains expected markers for scoring. This is a diagnostic channel with no secrecy claim against same-user readers.

Swift 6 builds with warnings as errors and strict signature checks pass. Python compilation and shell syntax pass. All seven frozen browser and helper images retain their hashes. No new grant, administrator access, global input hook, or device seizure occurs.

The next capture experiment should preserve a directly readable webpage and use a separate clear reference. Earlier window-sharing tests contain useful capture results, but their full-display and physical controls remain separate. A visible page must pass those checks together before any screenshot defense claim.
