import Foundation
import CoreGraphics

enum GeometryOperation: String {
    case move
    case shrink
}

enum WindowGeometryScope {
    static func permits(root: String, pid: Int32, path: String) -> Bool {
        pid > 1 && ["InspectableControl", "InternalKeyboardControl"].contains {
            path == root + "/dist/\($0).app/Contents/MacOS/\($0)"
        }
    }

    static func points(frame: CGRect, operation: GeometryOperation) -> (CGPoint, CGPoint)? {
        guard [frame.minX, frame.minY, frame.width, frame.height].allSatisfy(\.isFinite),
              frame.width >= 600, frame.height >= 400 else { return nil }
        switch operation {
        case .move:
            return (CGPoint(x: frame.midX, y: frame.minY + 12), CGPoint(x: frame.midX + 100, y: frame.minY + 72))
        case .shrink:
            return (CGPoint(x: frame.maxX - 2, y: frame.maxY - 2), CGPoint(x: frame.maxX - 142, y: frame.maxY - 92))
        }
    }
}
