# Live renderer reads on the combined preview

Milestone 138 restores effective Accessibility for the unchanged PreviewRendererReadProbe and runs one matched token-read comparison. The readable reference exposes its fresh page marker. The physically completed preview exposes no marker within the bounded scan. No input events or AX actions run, and no new preview submission occurs.

## Grant recovery

The user approves one reset of `Accessibility` for `research.agentfreebrowser.previewrendererread`. That exact command succeeds. The same pinned helper requests access again, and the user enables it. A fresh helper process reports effective access. The read comparison then uses that same image successfully.

No other app or permission resets. The helper is not rebuilt or re-signed. Its executable SHA-256 remains `18c7df1aba7af587ba002f52f38b4e07c6a0fd06be275493ce2d220fe4db8f8f`.

## Fresh physical session

The earlier preview PID 2892 ends under its original one-hour watchdog before the grant recovery completes. Its physical result does not transfer to a new process.

The unchanged preview opens as PID 35426 with a new private fixture. The user reports Task complete after physical keyboard navigation and entry. Device binding is present, and the independent fixture records exactly one accepted submission. The renderer read uses that same new process and image. The accepted count stays at one afterward.

## Read calibration and result

| Route | Fresh readable reference | Preview result |
| --- | --- | --- |
| Plain renderer application root | No renderer marker, despite host-tree disclosure | Not attempted |
| Bounded remote-token scan | Exact fresh marker recovered from renderer | No marker recovered from renderer or host |

The plain-root calibration supplies no candidate claim. The successful token route runs as a separate comparison with its own fresh reference. It does not bypass a failed reference within the plain-root comparison. Each owned helper and reference stops before the next stage.

The token helper scans IDs zero through 1,023 separately in the owned renderer and host. Both candidate queries complete without budget exhaustion. The renderer query visits four elements, resolves two token roots, and discards one foreign-owned element. The host query visits six elements and resolves five token roots. Neither query returns a research marker.

The result is `marker-not-recovered-in-bounded-scan`. It does not establish that every possible token is inaccessible. The helper sends no writes or presses, so it supplies no renderer-action prevention result. It also does not test Web Inspector attachment.

## Code and checks

`tools/calibrate_preview_renderer_read.py` runs one reference-only route with a private fixture. It requires approved, effective access before it opens a reference. `tools/run_preview_renderer_token_comparison.py` requires the exact physical declaration, process, and image before its matched comparison. It skips the candidate after failed calibration or foreground checks and reports incomplete scans as inconclusive.

All 12 Python checks pass, including failed-reference and cleanup stops, failed candidate activation, incomplete-scan scoring, and marker-recovery scoring. Python compilation passes. All 12 permissioned executable images retain their hashes. Browser and pinned helper sources remain unchanged.

All transient probes and readable references stop. LinearMouse and DockDoor remain running. No synthetic input test runs in that environment. The new preview and its private fixture remain live under their original one-hour watchdog. Their session file is `artifacts/preview-renderer-138/physical-session/session.json`. Its separate physical declaration is `artifacts/preview-renderer-138/physical-control.json`.

See [saved results](evidence/preview-renderer-live-results.json). Agent-free browsing remains unproven. Continuous capture on this exact preview, external inspector attachment, autonomous page actions, and broad website compatibility remain open. Earlier screenshot and native-input results retain their original session scopes.
