import Foundation

enum PreviewCapturePixels {
    static func containsColor(_ bytes: UnsafeRawBufferPointer, width: Int, height: Int, stride: Int) -> Bool? {
        guard (1...8192).contains(width), (1...8192).contains(height),
              stride >= width * 4, stride <= 65536, bytes.count >= height * stride else { return nil }
        let alpha = bytes[3]
        for row in 0..<height {
            let start = row * stride
            for pixel in 0..<width {
                let offset = start + pixel * 4
                if bytes[offset] != 0 || bytes[offset + 1] != 0 || bytes[offset + 2] != 0 { return true }
                if bytes[offset + 3] != alpha { return true }
            }
        }
        return false
    }
}
