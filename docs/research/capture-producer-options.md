# Next protected-pixel producer experiment

Research date: October 27, 2026. This note records the source research for the compressed producer. The [implementation findings](../compressed-rendering-findings.md) record its later live results.

## Existing experiment and the change to test

The earlier `Sources/Rendering/RenderApp.swift` producer takes a WKWebView snapshot, creates a BGRA or NV12 image buffer, wraps that uncompressed buffer, and displays it. Both protected variants failed direct-display visibility. The matched unprotected control remained visible. Compression is therefore a different producer path to test, not a proven fix. [Existing findings](../pixel-rendering-findings.md).

Apple explicitly documents that `AVSampleBufferDisplayLayer` accepts compressed frames. Its WWDC session describes the internal decoder and display queue. This supports a local H.264 comparison without a license server. The capture setting still comes from `preventsCapture`. Compression alone adds no DRM. [Apple display layer](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer), [Apple compressed-frame walkthrough](https://developer.apple.com/videos/play/wwdc2014/513/).

## Smallest defensible producer

1. Create a `VTCompressionSession` for H.264 at a fixed, even frame size. Submit image buffers with strictly increasing presentation timestamps. The encoder returns compressed frames through a callback. Preserve the returned sample's format description, timing, and dependency information. The callback already supplies a `CMSampleBuffer`, so a local encoder avoids a separate elementary-stream parser. [Apple encoder creation](https://developer.apple.com/documentation/videotoolbox/vtcompressionsessioncreate(allocator:width:height:codectype:encoderspecification:imagebufferattributes:compresseddataallocator:outputcallback:refcon:compressionsessionout:)), [Apple encode contract](https://developer.apple.com/documentation/videotoolbox/vtcompressionsessionencodeframe(_:imagebuffer:presentationtimestamp:duration:frameproperties:infoflagsout:outputhandler:)), [Apple callback](https://developer.apple.com/documentation/videotoolbox/vtcompressionoutputcallback).
2. Select low-latency rate control when creating the encoder. Apple documents no frame reordering or lookahead in that mode. Check each configuration result. Apple warns that encoders do not support every property. `RealTime=true` recommends timely encoding but does not guarantee it. [Apple low-latency mode](https://developer.apple.com/documentation/videotoolbox/kvtvideoencoderspecification_enablelowlatencyratecontrol), [Apple property support](https://developer.apple.com/documentation/videotoolbox/compression-properties), [Apple real-time hint](https://developer.apple.com/documentation/videotoolbox/kvtcompressionpropertykey_realtime).
3. Enqueue successful, nonempty encoder samples into `sampleBufferRenderer`. Use monotonic source timing even when requesting immediate display. Apple documents `DisplayImmediately` as a request to present as soon as possible instead of following presentation timestamps. Start with an unprotected control that visibly changes text, then repeat the same producer with capture prevention enabled. [Apple immediate-display attachment](https://developer.apple.com/documentation/coremedia/kcmsampleattachmentkey_displayimmediately).
4. Bound pending work and record encode errors, dropped frames, renderer errors, readiness, and external-protection state. Do not silently return to a clear WebView or clear layer after a failure. The initial test needs no interaction bridge.

A timing alternative is a host-clock-based control timebase whose media time matches the submitted timestamps. Apple's walkthrough shows both the timebase and feed control. This is useful if immediate presentation produces unclear results. [Apple timing walkthrough](https://developer.apple.com/videos/play/wwdc2014/513/).

## FairPlay assets are not ready playback credentials

Apple links encrypted and unencrypted test streams and a Server SDK containing development credentials. However, Technical Note TN2454 explicitly says development credentials cannot test actual protected-content playback. They support tests of the Key Security Module with SPC vectors and `verify_ckc`. A genuine FairPlay playback control therefore needs valid playback credentials and a working key-response path, or a separately authorized service that already supplies them. [Apple FairPlay resources](https://developer.apple.com/streaming/fps/), [Apple credential limits](https://developer.apple.com/library/archive/technotes/tn2454/_index.html).

The public FairPlay page says deployment credentials require Apple approval and a consumer streaming service. Downloading encrypted assets does not remove this prerequisite. Do not call a clear H.264 clip a FairPlay control.

## Supported alternatives and limits

The reviewed Apple APIs establish a capture flag on the sample-buffer display layer and FairPlay media playback. `AVSampleBufferVideoRenderer` supplies enqueue and diagnostics APIs, but its reviewed reference does not establish a second independent capture-protection mechanism. No reviewed source establishes a protected arbitrary-HTML option for WKWebView, CALayer, or Metal. This is a finding about these sources, not a universal impossibility claim. [Apple video renderer](https://developer.apple.com/documentation/avfoundation/avsamplebuffervideorenderer).

Chromium uses the same display layer and capture flag for protected video. Its April 2026 fix updates the flag when reusing layers. Thus, layer replacement and clear-to-protected transitions belong in capture tests. [Chromium fix](https://chromium.googlesource.com/chromium/src/+/51a8376f9f5ee7e0a2eb566d9b86687119e9ce0a%5E%21/).

Success requires physical visibility plus unreadable output in each tested external capture route. Black screenshots with black physical output remain a failed configuration. A visible compressed result would justify HTML snapshots next, followed by interaction and transition tests. It would not establish protection for every website or capture API.
