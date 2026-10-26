import CoreGraphics

@main
enum WindowGeometryScopeTests {
    static func main() {
        let root = "/research"
        for name in ["InspectableControl", "InternalKeyboardControl"] {
            precondition(WindowGeometryScope.permits(root: root, pid: 10, path: root + "/dist/\(name).app/Contents/MacOS/\(name)"))
        }
        for path in [root + "/dist/DeviceKeyboardExperiment.app/Contents/MacOS/DeviceKeyboardExperiment",
                     "/System/Applications/Safari.app/Contents/MacOS/Safari",
                     root + "/dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl.other"] {
            precondition(!WindowGeometryScope.permits(root: root, pid: 10, path: path))
        }
        let allowed = root + "/dist/InspectableControl.app/Contents/MacOS/InspectableControl"
        for pid in [Int32(-1), 0, 1] { precondition(!WindowGeometryScope.permits(root: root, pid: pid, path: allowed)) }
        let frame = CGRect(x: 100, y: 100, width: 1000, height: 740)
        for operation in [GeometryOperation.move, .shrink] {
            guard let (start, end) = WindowGeometryScope.points(frame: frame, operation: operation) else { preconditionFailure() }
            for step in 0...24 {
                let t = Double(step) / 24
                precondition(frame.contains(CGPoint(x: start.x + (end.x - start.x) * t, y: start.y + (end.y - start.y) * t)))
            }
        }
        precondition(WindowGeometryScope.points(frame: CGRect(x: 0, y: 0, width: 100, height: 100), operation: .shrink) == nil)
        print("Window geometry scope passed target exclusions and both 25-point bounded paths. No input was posted.")
    }
}
