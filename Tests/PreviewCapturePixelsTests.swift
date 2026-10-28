import Foundation

@main
enum PreviewCapturePixelsTests {
    static func main() {
        func colored(_ bytes: [UInt8], width: Int = 2, height: Int = 2, stride: Int = 8) -> Bool? {
            bytes.withUnsafeBytes { PreviewCapturePixels.containsColor($0, width: width, height: height, stride: stride) }
        }
        let opaque = Array(repeating: [UInt8](arrayLiteral: 0, 0, 0, 255), count: 4).flatMap { $0 }
        precondition(colored(opaque) == false)
        precondition(colored(Array(repeating: 0, count: 16)) == false)
        var alphaMask = opaque
        alphaMask[15] = 0
        precondition(colored(alphaMask) == true)
        for channel in 0..<3 {
            var changed = opaque
            changed[12 + channel] = 1
            precondition(colored(changed) == true)
        }
        precondition(colored([0, 0, 0, 255, 255, 255, 255, 255], width: 1, height: 1, stride: 8) == false)
        precondition(colored(Array(opaque.dropLast())) == nil)
        precondition(colored(opaque, width: 0) == nil)
        precondition(colored(opaque, height: 0) == nil)
        precondition(colored(opaque, stride: 4) == nil)
        precondition(colored(opaque, width: 8193) == nil)
        print("12 pixel-audit boundary checks passed.")
    }
}
