#if PIXEL_H264
import Foundation
import CoreMedia
import CoreVideo
import VideoToolbox

// The lock protects callback state. The caller reads it after CompleteFrames returns.
private final class EncodedOutput: @unchecked Sendable {
    private struct State {
        var samples: [CMSampleBuffer] = []
        var error: OSStatus = noErr
        var dropped = false
    }
    private let lock = NSLock()
    private var state = State()

    func receive(status: OSStatus, flags: VTEncodeInfoFlags, sample: CMSampleBuffer?) {
        lock.withLock {
            if status != noErr { state.error = status }
            if flags.contains(.frameDropped) { state.dropped = true }
            if let sample { state.samples.append(sample) }
        }
    }

    func take() throws -> CMSampleBuffer {
        try lock.withLock {
            guard state.error == noErr, !state.dropped, state.samples.count == 1,
                  let sample = state.samples.first, CMSampleBufferDataIsReady(sample) else {
                throw RenderFailure("Compressed frame unavailable: status=\(state.error) samples=\(state.samples.count) dropped=\(state.dropped)")
            }
            state.samples.removeAll()
            return sample
        }
    }
}

@MainActor
final class H264Frames {
    private let session: VTCompressionSession
    private let width: Int
    private let height: Int
    private var sequence: Int64 = 0
    let hardwareReadbackStatus: OSStatus
    let hardwareReadback: Bool?

    init(width: Int, height: Int) throws {
        guard width > 0, height > 0, width <= 4096, height <= 4096,
              width.isMultiple(of: 2), height.isMultiple(of: 2) else {
            throw RenderFailure("Unsupported compressed frame dimensions")
        }
        self.width = width
        self.height = height
        var created: VTCompressionSession?
        let specification: [CFString: Any] = [
            kVTVideoEncoderSpecification_RequireHardwareAcceleratedVideoEncoder: true,
            kVTVideoEncoderSpecification_EnableLowLatencyRateControl: true,
        ]
        let result = VTCompressionSessionCreate(allocator: kCFAllocatorDefault,
            width: Int32(width), height: Int32(height), codecType: kCMVideoCodecType_H264,
            encoderSpecification: specification as CFDictionary, imageBufferAttributes: nil,
            compressedDataAllocator: nil, outputCallback: nil, refcon: nil,
            compressionSessionOut: &created)
        guard result == noErr, let created else {
            throw RenderFailure("Required hardware encoder unavailable: \(result)")
        }
        session = created
        do {
            for (key, value): (CFString, CFTypeRef) in [
                (kVTCompressionPropertyKey_RealTime, kCFBooleanTrue),
                (kVTCompressionPropertyKey_MaxKeyFrameInterval, 1 as CFNumber),
                (kVTCompressionPropertyKey_ExpectedFrameRate, 5 as CFNumber),
                (kVTCompressionPropertyKey_AverageBitRate, 8_000_000 as CFNumber),
            ] {
                let status = VTSessionSetProperty(created, key: key, value: value)
                guard status == noErr else {
                    throw RenderFailure("Encoder property \(key) refused: \(status)")
                }
            }
            let status = VTCompressionSessionPrepareToEncodeFrames(created)
            guard status == noErr else { throw RenderFailure("Encoder preparation failed: \(status)") }
            var hardware: Unmanaged<CFTypeRef>?
            let readback = VTSessionCopyProperty(created,
                key: kVTCompressionPropertyKey_UsingHardwareAcceleratedVideoEncoder,
                allocator: kCFAllocatorDefault, valueOut: &hardware)
            let value = hardware?.takeRetainedValue() as? Bool
            guard (readback == noErr && value == true) || readback == kVTPropertyNotSupportedErr else {
                throw RenderFailure("Hardware encoder readback failed: \(readback)")
            }
            hardwareReadbackStatus = readback
            hardwareReadback = value
        } catch {
            VTCompressionSessionInvalidate(created)
            throw error
        }
    }

    isolated deinit { VTCompressionSessionInvalidate(session) }

    func encode(_ image: CVPixelBuffer) throws -> CMSampleBuffer {
        guard CVPixelBufferGetWidth(image) == width, CVPixelBufferGetHeight(image) == height else {
            throw RenderFailure("Compressed frame dimensions changed")
        }
        let output = EncodedOutput()
        let timestamp = CMTime(value: sequence, timescale: 5)
        let result = VTCompressionSessionEncodeFrame(session, imageBuffer: image,
            presentationTimeStamp: timestamp, duration: CMTime(value: 1, timescale: 5),
            frameProperties: [kVTEncodeFrameOptionKey_ForceKeyFrame: true] as CFDictionary,
            infoFlagsOut: nil) { status, flags, sample in
                output.receive(status: status, flags: flags, sample: sample)
            }
        guard result == noErr else { throw RenderFailure("Frame encoding failed: \(result)") }
        let completion = VTCompressionSessionCompleteFrames(session, untilPresentationTimeStamp: .invalid)
        guard completion == noErr else { throw RenderFailure("Frame completion failed: \(completion)") }
        let sample = try output.take()
        guard let format = CMSampleBufferGetFormatDescription(sample),
              CMFormatDescriptionGetMediaSubType(format) == kCMVideoCodecType_H264,
              CMTimeCompare(CMSampleBufferGetPresentationTimeStamp(sample), timestamp) == 0 else {
            throw RenderFailure("Unexpected compressed format or timestamp")
        }
        sequence += 1
        return sample
    }
}
#endif
