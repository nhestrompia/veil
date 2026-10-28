import Foundation
import Testing

@Test func uniformPixelIncludesAlpha() {
    let bytes: [UInt8] = [7, 18, 30, 255, 7, 18, 30, 255]
    #expect(bytes.withUnsafeBytes { PreviewCompositorPixels.uniformBGRA($0, width: 2, height: 1, stride: 8) } == [7, 18, 30, 255])
}

@Test(arguments: [0, 1, 2, 3]) func spatialDifferenceCannotPass(channel: Int) {
    var bytes = [UInt8](repeating: 0, count: 8)
    bytes[4 + channel] = 1
    #expect(bytes.withUnsafeBytes { PreviewCompositorPixels.uniformBGRA($0, width: 2, height: 1, stride: 8) } == [])
}

@Test func ignoresRowPadding() {
    let bytes: [UInt8] = [1, 2, 3, 4, 99, 98, 97, 96, 1, 2, 3, 4, 95, 94, 93, 92]
    #expect(bytes.withUnsafeBytes { PreviewCompositorPixels.uniformBGRA($0, width: 1, height: 2, stride: 8) } == [1, 2, 3, 4])
}

@Test(arguments: [(0, 1, 4), (1, 0, 4), (1, 1, 3), (8193, 1, 32772), (1, 1, 65537), (2, 2, 8)])
func rejectsInvalidBuffer(dimensions: (Int, Int, Int)) {
    let bytes = [UInt8](repeating: 0, count: 8)
    #expect(bytes.withUnsafeBytes { PreviewCompositorPixels.uniformBGRA($0, width: dimensions.0, height: dimensions.1, stride: dimensions.2) } == nil)
}
