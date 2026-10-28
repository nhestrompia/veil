# Unfiltered capture after filter changes

Milestone 130 tests whether a running display stream exposes the page after its application exclusion filter changes. The restricted image exposes only the owned backdrop in all 24 sampled frames. Both clear references expose their page marker in all 48 sampled frames. The tested sequence does not recover the restricted page.

| Stream stage | Clear before | Restricted | Clear after |
| --- | --- | --- | --- |
| Exclude capture helper | Page in 8/8 | Backdrop in 8/8 | Page in 8/8 |
| Include capture helper | Page in 8/8 | Backdrop in 8/8 | Page in 8/8 |
| Exclude capture helper again | Page in 8/8 | Backdrop in 8/8 | Page in 8/8 |

The stream captures an unfiltered display crop. Only the capture helper enters or leaves the exclusion list. The target and backdrop remain included. Each stage lasts two seconds and saves at most eight complete frames. The restricted stream observes 66, 67, and 67 complete frames across the stages. The scorer examines the saved samples, not every observed frame. All three streams stop without an error.

The helper checks identity, foreground state, opaque owned coverage, window order, and overlays around capture. The crop stays inside the owned research windows. Local image inspection agrees with the marker scorer. The restricted sample shows the teal backdrop label. The clear sample shows the address, fixture marker, and completed form.

## Exact images and physical baseline

The controller restores the archived compact images from milestone 125. It checks their hashes and original bundle signatures without signing them again.

| Image | SHA-256 |
| --- | --- |
| Restricted | `c14248c3ac02acac3bbfe3130479744c2e8780a13a0c50a1534af1b5e7789f4a` |
| Clear | `be47fd551b98123a64c581b264d93595270ee8f9f6895f19ce421c7cb5f81e18` |

The user reported physical readability for this exact restricted executable in milestone 125. No new physical observation occurs during milestone 130. The diagnostic uses a target above an opaque backdrop at high window levels. These window levels do not establish normal browser usability.

A fixed internal key sequence completes the disposable form once per host. It uses no device reader or system input. This sequence is a renderer control, not evidence of human input or external action resistance.

## Permission and failed controls

The approved request and one authorized retry both report access off. The user then confirms the exact app's switch is on. A fresh LaunchServices preflight reports Screen Recording granted. The helper's executable and source remain unchanged. No permission reset or administrator action runs.

Three earlier clear controls stop after foreground changes. The first saves no frame. The other two recover eight page samples in the initial stage. All stop their streams and launch no restricted candidate. These failed controls do not count as protection. Recorded foreground process metadata identifies UserNotificationCenter in the first failure and Chrome in the later failures. No dialog text or unrelated page content enters the record. The cause of those focus changes remains unknown.

A new coordinator can activate only the verified research target. It waits at most five seconds for the capture helper, observes at most eight seconds, and permits at most three activations. A 15-second alarm bounds the process. It stops on recognized system-dialog foreground identities. It sends no input and installs no hooks. Its unrelated-process refusal check passes.

The successful comparison records zero activations in every trial. The coordinator therefore does not explain why this comparison kept focus. Native capture checks remain unchanged and mandatory.

## Cleanup and limits

All recorded research process IDs are absent. Each host and fixture stops, and each fixture port is closed. Nine permissioned helper images retain their hashes. Both capture helpers also retain their source hashes. Swift 6 compilation with warnings as errors, Python compilation, and shell syntax checks pass.

Coverage checks and capture are not atomic. Queued frames can cross a filter update. Sparse samples cannot prove continuous exclusion. This test covers helper exclusion changes on one local fixture and one macOS configuration. It does not cover capture-type changes, QuickTime, long recordings, resizing, fullscreen, multiple displays, or all websites. General browser integration and external input attacks remain separate work. Agent-free browsing remains unproven.

See the [saved results](evidence/compositor-refresh-live-results.json), [clear sample](evidence/compositor-refresh-clear.png), and [restricted sample](evidence/compositor-refresh-backdrop.png). Raw artifacts are in `artifacts/compositor-refresh-130/20261028-coordinated`.
