# Enforcing capture protection

Research date: October 27, 2026. This note separates documented behavior from proposed experiments. It reports no new live result.

## Browser control and operating-system control

Apple calls `NSWindow.SharingType.none` a legacy constant that macOS no longer uses. Its discussion says not to use the value to hide captured content and points to FairPlay Streaming. Thus, owning the browser window does not establish authority over another process's capture output. [Apple window-sharing reference](https://developer.apple.com/documentation/appkit/nswindow/sharingtype-swift.enum/none).

ScreenCaptureKit supplies capture streams and lets the capturing application choose content through its filter. A filter in our application does not configure a separate application's stream. This is an architectural inference from the documented ownership of streams and filters. [Apple ScreenCaptureKit](https://developer.apple.com/documentation/screencapturekit), [Apple content filters](https://developer.apple.com/documentation/screencapturekit/sccontentfilter).

For video presentation, Apple explicitly exposes `AVSampleBufferDisplayLayer.preventsCapture`. The layer accepts compressed or uncompressed video frames. FairPlay separately supplies encrypted media playback through HTTP Live Streaming. Neither cited API establishes protection for a normal HTML view. [Apple display layer](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer), [Apple FairPlay Streaming](https://developer.apple.com/streaming/fps/).

## GPU fallback does not mean encryption defeat

A capturable decoded image does not establish that an attacker defeated DRM encryption or obtained a content key. Decryption, decoding, and protected presentation are distinct steps.

Chromium supplies a concrete macOS example. Commit `51a8376f` fixed reused video layers that retained an old `preventsCapture` value. Chromium's description says this let DRM-protected content enter screen recordings. The fix updates the protection flag and tests transitions between clear and protected media. The failure concerned presentation state, not a reported defeat of content decryption. [Chromium fix and tests](https://chromium.googlesource.com/chromium/src/+/51a8376f9f5ee7e0a2eb566d9b86687119e9ce0a%5E%21/).

The user's GPU-setting observation therefore needs a specific reproduction before we attribute its cause. It could expose a different presentation path. It does not by itself identify a general DRM bypass.

## What this app can refuse

An app that creates its own `VTDecompressionSession` can require hardware decoding. Apple states that `kVTVideoDecoderSpecification_RequireHardwareAcceleratedVideoDecoder=true` makes session creation fail when no suitable hardware decoder is available. [Apple hardware requirement](https://developer.apple.com/documentation/videotoolbox/kvtvideodecoderspecification_requirehardwareacceleratedvideodecoder).

That key controls our decoder session. It does not attest protected presentation or directly configure the internal decoder of the current sample-buffer display layer. Hardware decoding alone is not evidence of capture exclusion.

A proposed browser policy can refuse an unsupported configuration and never display a clear fallback. That policy needs a reliable condition to test. Layer readiness and an `obscured=false` value cannot prove human visibility or capture protection, as this project's failed BGRA and NV12 trials show. [Existing project findings](../pixel-rendering-findings.md).

## Next experiment

1. Establish a physically visible protected-media control with a legitimate test stream and matching unprotected control. Record the player, stream, OS, display, and protection settings. FairPlay development assets require the documented SDK and key-request setup. If unavailable, report that prerequisite instead of calling an unencrypted clip a FairPlay control. [Apple FairPlay resources](https://developer.apple.com/streaming/fps/).
2. Compare that control with compressed, application-generated frames in a protected sample-buffer layer. Start with changing text, then HTML snapshots. This changes the failed uncompressed presentation path. Whether it restores visible protected output is a hypothesis.
3. Test capture while resizing, entering fullscreen, replacing layers, and switching clear/protected content. Include display capture and continuous recording. Chromium's reuse bug makes transition tests necessary.
4. Add deliberate failure cases. Refuse rendering when the required decoder or presentation configuration fails. Check that no clear fallback or stale unprotected layer appears.

Success requires visible content for the person and unreadable content through each tested capture route. A media-only result remains a media result. Extending it to interactive HTML still requires an input bridge, acceptable latency, and separate checks for semantic reads and automation.
