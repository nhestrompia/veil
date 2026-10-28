import Foundation

enum PreviewCompositorPixels {
    // Uniform output cannot encode the page's spatial marker through RGB or alpha.
    static func uniformBGRA(_ bytes: UnsafeRawBufferPointer, width: Int, height: Int, stride: Int) -> [UInt8]? {
        guard (1...8192).contains(width), (1...8192).contains(height),
              stride >= width * 4, stride <= 65536, bytes.count >= height * stride else { return nil }
        let pixel = Array(bytes.prefix(4))
        for row in 0..<height {
            for column in 0..<width {
                let offset = row * stride + column * 4
                for channel in 0..<4 where bytes[offset + channel] != pixel[channel] { return [] }
            }
        }
        return pixel
    }
}
