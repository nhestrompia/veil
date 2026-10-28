# Renderer reads on the combined preview

Milestone 136 prepares a new read-only probe for the unchanged AgentFreeBrowserPreview. Live ownership checks identify its WebKit renderer and a fresh readable control's renderer. No accessibility read, input event, or website action runs. The new helper has no Accessibility grant, and no permission request runs.

The existing RendererAXProbe cannot target the preview. Its scope permits only two earlier app identities. Rebuilding that granted helper would change its reviewed image. The new PreviewRendererReadProbe has a separate identity and leaves all existing grants intact.

## Target and data limits

The helper accepts exactly two hosts, with fixed bundle IDs, executable paths, and SHA-256 hashes. They are AgentFreeBrowserPreview and InspectableControl. It checks process start times, user identity, Apple's WebKit executable path, and the OS responsibility relationship. It checks element ownership before each attribute read and discards foreign elements.

The read mode traverses only owned host and renderer elements. A separate token mode tries at most 1,024 IDs per process. These private token APIs are an attack-tool experiment, not a browser dependency or supported guarantee. Token construction reuses the unchanged earlier [renderer scope](../Sources/Diagnostics/RendererProcessScope.swift).

The complete query has a 12-second budget and a 20-second native alarm. It permits at most four renderer processes and 500 visited elements per process. Budget exhaustion marks the traversal incomplete. The probe saves role counts and fixed `AFB-` marker matches. It saves no raw page text, titles, typed text, or key codes. It sends no AX actions or synthetic input and installs no hooks.

The explicit `request-accessibility` command is separate from every discovery and read command. Ordinary launches do not prompt. The [permission manifest](evidence/preview-renderer-read-permission-manifest.json) records the exact final image and its unexecuted request command.

## Preparation results

| Check | Observed result |
| --- | --- |
| Preview ownership | Host PID 2892, WebKit renderer PID 3422, pinned host hash matches |
| Fresh readable reference | One owned WebKit renderer, no fixture submission, cleanup passes |
| Unrelated target | Refused before accessibility queries |
| Final runner without grant | Stops before any reference or AX read |
| Final helper permission request | Not executed |
| New preview actions | Zero |
| Cleanup | No probe or reference remains. Both modifier apps remain running. |

Seventeen Swift policy checks and seven Python calibration checks pass. Swift 6 compilation treats warnings as errors. Python compilation and strict code-signature checks pass. All 11 earlier permissioned executable images and the browser source hashes remain unchanged.

An earlier request-mode build failed because the SDK imports a constant as mutable shared state. The outer command sequence continued and retained the prior helper image. No request ran. That unapproved pin and image are archived. The corrected import compiles, and the final image repeats the discovery and permission-gate checks. The final executable hash is `18c7df1aba7af587ba002f52f38b4e07c6a0fd06be275493ce2d220fe4db8f8f`.

## Inspector client check

A separate command-line tool reads installed Objective-C class metadata without creating an inspector or contacting its relay. This Mac exposes the expected remote-inspector frontend classes and selectors. That result establishes interface availability only. It neither attaches to the preview nor supplies a debugger transport.

Current WebKit source uses XPC for Cocoa remote inspection. The earlier absence of TCP listeners therefore cannot establish inspection prevention. The official Safari route and the standalone-client limits are documented in the [primary-source review](research/preview-inspection-next-step.md). No Safari setting changes.

## Approved request and stale signature

Checkpoint 137 issues the approved request for the pinned final helper. The user then reports Enabled in System Settings. Two fresh LaunchServices preflights still report no effective Accessibility access. The helper sends no input and performs no AX reads.

TCC logs explicitly report a failed code-requirement match for this bundle. They contain both an older stored code hash and the current helper's code hash. This is a stale grant identity, not a renderer blocking result. The final executable hash remains unchanged. No permission reset runs.

An app-only reset and another request for the same pinned app need separate approval. The exact proposed command is `tccutil reset Accessibility research.agentfreebrowser.previewrendererread`. It affects only this helper's Accessibility entry. No other permission or app reset is proposed. See [grant evidence](evidence/preview-renderer-read-grant-results.json).

The earlier unapproved helper launches explain a possible source of the stale identity. They queried trust before the final image existed. Future helper preparation must complete and pin the final signature before any trust query or permission request. This checkpoint does not change the frozen helper to address that preparation mistake.

## Next live comparison

The new helper has user approval for macOS Accessibility, but its grant remains ineffective. This is a broad system permission. The helper's reviewed code limits reads to the two pinned research apps and their owned renderers. Do not rebuild or re-sign it after approval. Do not refresh any existing grant.

After approval and effective access, run `tools/run_preview_renderer_reads.py` with the live session and its separate physical-control record. Each mode requires a fresh readable reference to recover its own renderer marker before the candidate runs. Host-only disclosure does not calibrate a renderer read. Failed references skip the candidate. Incomplete candidate queries and recovered markers stop later modes. No input posting or modifier-app pause is needed.

The runner checks that the same physical browser process and image remain active. Its one-hour session watchdog still applies. If that session expires, a new physical control is needed for same-session claims. This preparation establishes no renderer-read prevention or agent-free result.

See [saved preparation results](evidence/preview-renderer-read-preparation-results.json). Full discovery, permission-gate, and metadata records remain in `artifacts/preview-renderer-136/`.
