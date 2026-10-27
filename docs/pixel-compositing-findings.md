# Protected presentation fails physical visibility

Milestone 123, October 27, 2026. The combined protected browser fails its physical visibility check. A separate source-clipping diagnostic also fails. The original H.264 protected app is black on the direct display in a fresh test. Its earlier readability report is not reproducible now.

## Measured results

| Target | Physical report | Task result | External observation |
| --- | --- | --- | --- |
| Frozen combined browser | Black window or page | Physical keys bind and load the page. No accepted form action. | AX returns app and window titles. Window capture has a black media area. |
| Frozen clear routing control | Address and webpage visible | One action through internal keys | The saved image shows the page and address. |
| Source-only clipping diagnostic | Black | One action through internal keys | Three capture routes return images without the marker. |
| Original H.264 protected app | Black, including a later solo retest | No input bridge exists | Window capture has a black media area in the first retest. |

The source-only diagnostic clips the hidden WebView and address in a separate sibling. The protected display is a sibling of that explicitly clipped source container. The diagnostic reports ready=true, obscured=false, and renderer status 1. It still appears black to the user. This attempted layout change does not restore visibility. It does not establish the root cause.

The new image also offers the original root-clipping layout for later comparisons. That diagnostic mode was not run in this milestone. Only the source-only mode has a new physical observation. Its internal keys establish page rendering and routing, not human input or agent resistance.

A display query reports one active, online, built-in, non-mirrored display. It saves no display name or serial number. These flags do not establish output protection.

## Source checks and limits

Apple documents capture protection and external-output obscuring as distinct properties of [AVSampleBufferDisplayLayer](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer). Neither readiness nor a successful enqueue proves physical readability. The local SDK header supplies no stronger guarantee for this case.

[Chromium's compositor](https://chromium.googlesource.com/chromium/src/+/master/ui/accelerated_widget_mac/ca_renderer_layer_tree.mm) also sets `preventsCapture` for protected video. Its pixel-buffer enqueue path does not establish that arbitrary HTML in this prototype will remain visible. It supplies a reference implementation, not evidence that our output works.

Swift 6 typechecking of the production branch passes with warnings as errors. The separate diagnostic build and strict signature check pass. Python compilation and shell syntax pass. All seven frozen browser/helper images retain their hashes. No new permission, global input hook, device seizure, administrator access, or unrelated process change occurs.

The clear and source-only sessions stop their owned apps and fixtures after their observations. The original app stops after its observation. The first protected session stops at its original fifteen-minute deadline. A second original-app session starts only after a preflight finds no remaining research host. The user again reports black before any screenshot runs in that session. That session also stops after its observation. All five owned app hosts and fixtures report stopped.

The solo retest excludes concurrent research renderers as the explanation for this observation. The next required result is a person-readable protected page and address, with the exact marker confirmed. Only then can black external captures count as useful protection. The current result fails the browser usability requirement and remains unsuitable for an agent-free claim.
