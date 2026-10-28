import CoreImage
import CoreMedia
import Foundation
import ScreenCaptureKit

// The output queue and main actor share only immutable images and status values under this lock.
private final class FirstCompleteFrame: NSObject, SCStreamOutput, @unchecked Sendable {
    private let lock = NSLock()
    private var frame: CGImage?
    private var statuses: Set<Int> = []

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of outputType: SCStreamOutputType) {
        guard outputType == .screen, sampleBuffer.isValid,
              let attachments = CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]],
              let status = attachments.first?[.status] as? Int else { return }
        let needsImage = lock.withLock {
            statuses.insert(status)
            return frame == nil
        }
        guard needsImage, SCFrameStatus(rawValue: status) == .complete,
              let buffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let image = CIImage(cvPixelBuffer: buffer)
        guard let copied = CIContext().createCGImage(image, from: image.extent) else { return }
        lock.withLock { if frame == nil { frame = copied } }
    }

    func image() -> CGImage? { lock.withLock { frame } }
    func observedStatuses() -> [Int] { lock.withLock { statuses.sorted() } }
}

@MainActor
func firstCompleteStreamFrame(filter: SCContentFilter, configuration: SCStreamConfiguration) async throws -> CGImage {
    configuration.minimumFrameInterval = CMTime(value: 1, timescale: 10)
    configuration.queueDepth = 3
    configuration.capturesAudio = false
    let output = FirstCompleteFrame()
    let stream = SCStream(filter: filter, configuration: configuration, delegate: nil)
    try stream.addStreamOutput(output, type: .screen, sampleHandlerQueue: DispatchQueue(label: "research.first-screen-frame"))
    try await stream.startCapture()
    do {
        for _ in 0..<40 {
            if let image = output.image() {
                try await stream.stopCapture()
                return image
            }
            try await Task.sleep(for: .milliseconds(100))
        }
        throw ProbeFailure("No complete screen frame within four seconds; statuses=\(output.observedStatuses())")
    } catch {
        try? await stream.stopCapture()
        throw error
    }
}
