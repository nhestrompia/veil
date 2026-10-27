#if PIXEL_H264
import Foundation
import CoreMedia
import CoreVideo
import VideoToolbox

// The lock protects callback state. The caller reads it after asynchronous decoding finishes.
private final class DecodedOutput: @unchecked Sendable {
    private struct State {
        var image: CVPixelBuffer?
        var status: OSStatus = noErr
        var count = 0
    }
    private let lock = NSLock()
    private var state = State()

    func receive(status: OSStatus, image: CVPixelBuffer?) {
        lock.withLock {
            state.status = status
            state.image = image
            state.count += 1
        }
    }

    func take() throws -> CVPixelBuffer {
        try lock.withLock {
            guard state.status == noErr, state.count == 1, let image = state.image else {
                throw RenderFailure("Decoded image unavailable: \(state.status)")
            }
            state.image = nil
            return image
        }
    }
}

@MainActor
enum CompressedSmoke {
    static func run() throws {
        let encoder = try H264Frames(width: 320, height: 240)
        var rows: [[String: Any]] = []
        for index in 0..<3 {
            let left = UInt8(40 + index * 20)
            let right = UInt8(180 - index * 20)
            let sample = try encoder.encode(buffer(left: left, right: right))
            guard let format = CMSampleBufferGetFormatDescription(sample),
                  let bytes = CMSampleBufferGetDataBuffer(sample) else {
                throw RenderFailure("Encoded data absent")
            }
            var decoder: VTDecompressionSession?
            let created = VTDecompressionSessionCreate(allocator: kCFAllocatorDefault,
                formatDescription: format,
                decoderSpecification: [kVTVideoDecoderSpecification_RequireHardwareAcceleratedVideoDecoder: true] as CFDictionary,
                imageBufferAttributes: [kCVPixelBufferPixelFormatTypeKey: kCVPixelFormatType_32BGRA] as CFDictionary,
                outputCallback: nil, decompressionSessionOut: &decoder)
            guard created == noErr, let decoder else { throw RenderFailure("Hardware decoder unavailable: \(created)") }
            defer { VTDecompressionSessionInvalidate(decoder) }
            let output = DecodedOutput()
            let decoded = VTDecompressionSessionDecodeFrame(decoder, sampleBuffer: sample, flags: [], infoFlagsOut: nil) {
                status, _, image, _, _ in output.receive(status: status, image: image)
            }
            guard decoded == noErr else { throw RenderFailure("Decode failed: \(decoded)") }
            let waited = VTDecompressionSessionWaitForAsynchronousFrames(decoder)
            guard waited == noErr else { throw RenderFailure("Decode wait failed: \(waited)") }
            let image = try output.take()
            let luma = try brightness(image, x: 80)
            let other = try brightness(image, x: 240)
            let expectedLeft = Double(Int(left) - 16) * 255 / 219
            let expectedRight = Double(Int(right) - 16) * 255 / 219
            guard abs(luma - expectedLeft) < 15, abs(other - expectedRight) < 15 else {
                throw RenderFailure("Decoded content differs from source: \(luma), \(other)")
            }
            var hardware: Unmanaged<CFTypeRef>?
            let checked = VTSessionCopyProperty(decoder, key: kVTDecompressionPropertyKey_UsingHardwareAcceleratedVideoDecoder,
                allocator: kCFAllocatorDefault, valueOut: &hardware)
            let hardwareValue = hardware?.takeRetainedValue() as? Bool
            guard (checked == noErr && hardwareValue == true) || checked == kVTPropertyNotSupportedErr else {
                throw RenderFailure("Hardware decoder readback failed: \(checked)")
            }
            rows.append(["frame": index, "bytes": CMBlockBufferGetDataLength(bytes),
                         "pts": CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample)),
                         "leftBrightness": luma, "rightBrightness": other,
                         "hardwareDecoderRequired": true, "hardwareDecoderReadbackStatus": checked,
                         "hardwareDecoderReadback": hardwareValue.map { $0 as Any } ?? NSNull(),
                         "contentMatched": true])
        }
        let changedSize = try buffer(left: 40, right: 180, width: 322)
        var changedSizeRefused = false
        do { _ = try encoder.encode(changedSize) }
        catch { changedSizeRefused = true }
        guard changedSizeRefused else { throw RenderFailure("Changed frame size was not refused") }
        let report: [String: Any] = ["status": "passed", "codec": "H264", "frames": rows,
            "changedSizeRefused": changedSizeRefused, "hardwareEncoderRequired": true,
            "hardwareEncoderReadbackStatus": encoder.hardwareReadbackStatus,
            "hardwareEncoderReadback": encoder.hardwareReadback.map { $0 as Any } ?? NSNull(),
            "captureTested": false, "physicalVisibilityVerified": false, "encryptedMedia": false]
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    }

    private static func buffer(left: UInt8, right: UInt8, width: Int = 320) throws -> CVPixelBuffer {
        var value: CVPixelBuffer?
        let allocated = CVPixelBufferCreate(kCFAllocatorDefault, width, 240,
            kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,
            [kCVPixelBufferIOSurfacePropertiesKey: [:]] as CFDictionary, &value)
        guard allocated == kCVReturnSuccess, let value,
              CVPixelBufferLockBaseAddress(value, []) == kCVReturnSuccess else {
            throw RenderFailure("Smoke pixel allocation failed")
        }
        defer { CVPixelBufferUnlockBaseAddress(value, []) }
        for plane in 0..<2 {
            guard let base = CVPixelBufferGetBaseAddressOfPlane(value, plane) else {
                throw RenderFailure("Smoke plane unavailable")
            }
            let stride = CVPixelBufferGetBytesPerRowOfPlane(value, plane)
            let rows = CVPixelBufferGetHeightOfPlane(value, plane)
            for y in 0..<rows {
                let row = base.advanced(by: y * stride)
                if plane == 0 {
                    memset(row, Int32(left), width / 2)
                    memset(row.advanced(by: width / 2), Int32(right), width - width / 2)
                } else { memset(row, 128, width) }
            }
        }
        return value
    }

    private static func brightness(_ image: CVPixelBuffer, x: Int) throws -> Double {
        guard CVPixelBufferGetPixelFormatType(image) == kCVPixelFormatType_32BGRA,
              CVPixelBufferGetWidth(image) == 320, CVPixelBufferGetHeight(image) == 240,
              CVPixelBufferLockBaseAddress(image, .readOnly) == kCVReturnSuccess else {
            throw RenderFailure("Unexpected decoded image")
        }
        defer { CVPixelBufferUnlockBaseAddress(image, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddress(image) else { throw RenderFailure("Decoded pixels unavailable") }
        let pixel = base.advanced(by: 120 * CVPixelBufferGetBytesPerRow(image) + x * 4).assumingMemoryBound(to: UInt8.self)
        return (Double(pixel[0]) + Double(pixel[1]) + Double(pixel[2])) / 3
    }
}
#endif
