# Capture exclusion and physical visibility

Research date: 2026-10-23. Sources are public Apple APIs, the installed macOS 27 SDK, and Chromium source code. This report adds no runtime results.

## Current BGRA output fails physical visibility

The parent experiment reports that the control marker appears in window, display, and system captures. The corresponding protected region is black in those captures. Both renderers report `.rendering`. The user confirms that the protected page is also black when viewed directly on the Mac's built-in or attached display.

This evidence establishes different captured output between the two builds. It also rejects the current BGRA configuration as useful browser protection. The person cannot read its protected page.

The display configuration may reject the protected presentation. The protected uncompressed producer may fail to produce visible output. These are hypotheses, not diagnosed causes. A remote viewing path does not explain the confirmed direct observation.

## Apple documents compressed and uncompressed input

`AVSampleBufferDisplayLayer` accepts compressed or uncompressed video frames. Its `preventsCapture` property controls protection against screen capture. The public property declaration does not state a FairPlay, encryption, entitlement, compressed-input, or HDCP prerequisite. That absence supports a public experiment. It does not establish that every pixel format works on every display configuration. [Apple display-layer API](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer), [Apple capture-protection property](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer/preventscapture)

The installed header requires IOSurface backing for `CMSampleBuffer` objects that wrap `CVPixelBuffer` objects. `PixelDisplay.present` requests that backing with `kCVPixelBufferIOSurfacePropertiesKey`. It creates an image format description, wraps the image buffer, sets `kCMSampleAttachmentKey_DisplayImmediately`, and enqueues through `sampleBufferRenderer`. This sequence matches the documented producer shape. The runtime still needs an explicit non-nil `CVPixelBufferGetIOSurface` check.

The header says `DisplayImmediately` replaces prior images regardless of their timestamps. Consequently, presentation time zero is not the leading explanation while that attachment takes effect. The same producer displays readable content with capture prevention disabled. This control reduces the likelihood of a general snapshot, geometry, or bitmap failure. It cannot rule out a difference inside the protected composition path.

The SDK file is `System/Library/Frameworks/AVFoundation.framework/Headers/AVSampleBufferDisplayLayer.h` beneath the root returned by `xcrun --show-sdk-path`. Its enqueue comments contain both the backing requirement and the immediate-display behavior.

## Rendering status does not prove visible output

The renderer's `.rendering` status means the object can enqueue and render sample buffers. It does not attest the pixels that reach a person's display. Apple exposes a separate `isReadyForDisplay` property. The installed header says a layer has no user-visible content while that property is false. It becomes true when the first video frame is ready for display. The property is available from macOS 14.4. [Apple readiness property](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer/isreadyfordisplay)

The relevant observations are:

| Observation | What the observation establishes | What it leaves unresolved |
| --- | --- | --- |
| `renderer.status == .rendering` | The renderer accepts its active role. | Actual visibility and capture exclusion. |
| `display.isReadyForDisplay == false` | No frame is ready for user-visible display. | Why the frame is absent. |
| `display.isReadyForDisplay == true` | A first frame reached display readiness. | Whether a particular physical or remote display shows it. |
| `renderer.error` and `requiresFlushToResumeDecoding` | A reported renderer error or recovery requirement. | An omitted capture with no renderer error. |
| `CVPixelBufferGetIOSurface(buffer) != nil` | The allocated buffer has IOSurface backing. | Protected presentation support for that buffer. |

`AVSampleBufferDisplayLayerReadyForDisplayDidChangeNotification` reports readiness changes. The header says readiness is not key-value observable. A delayed observation and the notification are more useful than a synchronous status read immediately after enqueue.

## External protection is a separate content requirement

`isOutputObscuredDueToInsufficientExternalProtection` reports whether the system obscures decoded output because the display configuration lacks the required external protection. The installed header makes the requirements content-dependent. Those requirements are inherent to the media and cannot be specified externally. The property is false when the content requires no external protection. [Apple external-protection property](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer/isoutputobscuredduetoinsufficientexternalprotection)

This property is available from macOS 11.3. `AVSampleBufferDisplayLayerOutputObscuredDueToInsufficientExternalProtectionDidChangeNotification` reports its changes. A true value supports an external-protection diagnosis. A false value does not prove that every display or capture route must show the layer. The flag describes a particular reason for obscuring content.

High-bandwidth Digital Content Protection, or HDCP, matters for media that requires a protected external connection. The reviewed API contracts do not establish that this project's generated BGRA samples carry such a requirement. Adding FairPlay or assuming an HDCP failure before reading the flag would skip the useful diagnostic distinction.

## A remote view can show the excluded capture

Apple describes protected media as absent from FaceTime screen sharing. That is an example of a person seeing a different result through a capture path. The session concerns shared media and includes iOS guidance. It does not specify this macOS layer's behavior for every remote desktop or virtual display. [Apple Group Activities session](https://developer.apple.com/videos/play/wwdc2021/10184/)

No reviewed primary source enumerates `preventsCapture` behavior across macOS Screen Sharing, Apple Remote Desktop, AirPlay, Sidecar, virtual displays, DisplayLink, and third-party remote desktops. A black remote view is therefore consistent with capture exclusion, but the current evidence does not diagnose that cause.

The user supplied the decisive direct observation for this BGRA pilot and reported black output. Future producer comparisons need the same observation. Reading another screenshot, a T3 preview, a recording, or a remote desktop cannot establish physical visibility.

## Compare NV12 before adding an encoder

Chromium offers useful implementation evidence. Its macOS renderer wraps a `CVPixelBuffer` in a `CMSampleBuffer`, sets immediate display, and enqueues it into this layer. Its compositor sets `preventsCapture` for protected content. This supports an uncompressed producer comparison without a DRM license system. It does not prove that arbitrary clear buffers become physically visible when marked protected. [Chromium compositor implementation](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/ui/accelerated_widget_mac/ca_renderer_layer_tree.mm)

Chromium's format table marks NV12 and other YUV formats as suitable for AV sample-buffer display. Its BGRA entry lacks that flag. This is Chromium's policy, not an Apple declaration that protected BGRA is unsupported. Still, an IOSurface-backed NV12 producer is a useful smaller experiment before compressed video. The producer must display fresh text, with matched protected and unprotected cases. [Chromium IOSurface format table](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/ui/gfx/mac/io_surface.cc)

A compressed H.264 producer is a later isolation test. Apple's display-layer session describes compressed samples and the internal decode to pixel buffers. The comparison could distinguish direct BGRA presentation from the media decode path. No reviewed contract promises that compression fixes protected visibility. [Apple direct video access session](https://developer.apple.com/videos/play/wwdc2014/513/)

## Next experiments in order

1. Record delayed readiness, external-protection state, renderer errors, recovery state, and actual IOSurface backing for both builds.
2. Compare an IOSurface-backed NV12 producer with the same protection setting.
3. Get a direct physical-display observation for both NV12 builds with fresh content.
4. If necessary, compare a locally generated H.264 producer with matched controls and no FairPlay content.
5. Reject any configuration that remains unreadable to the person. A blank renderer cannot satisfy the browser goal.

Capture exclusion can proceed to interaction research only after physical visibility succeeds. The result must retain its exact OS, display, producer format, and capture-method limits.
