import AppKit
import Foundation

// This tool only pauses the two apps approved for the native input comparison.
let targets = [
    (id: "com.lujjjh.LinearMouse", path: "/Applications/LinearMouse.app"),
    (id: "com.ethanbills.DockDoor", path: "/Applications/DockDoor.app")
]
guard getuid() != 0, CommandLine.arguments.count == 3 else { exit(2) }
let operation = CommandLine.arguments[1]
let recordURL = URL(fileURLWithPath: CommandLine.arguments[2])

func matches(_ target: (id: String, path: String)) -> [NSRunningApplication] {
    NSRunningApplication.runningApplications(withBundleIdentifier: target.id).filter {
        $0.bundleURL?.standardizedFileURL.path == target.path
            && $0.executableURL?.standardizedFileURL.path == target.path + "/Contents/MacOS/" + URL(fileURLWithPath: target.path).deletingPathExtension().lastPathComponent
    }
}

if operation == "pause" {
    guard !FileManager.default.fileExists(atPath: recordURL.path) else { exit(3) }
    let original = targets.filter { !matches($0).isEmpty }.map(\.id)
    try JSONEncoder().encode(original).write(to: recordURL, options: .atomic)
    for target in targets where original.contains(target.id) {
        for app in matches(target) {
            let requested = app.terminate()
            let deadline = Date().addingTimeInterval(5)
            while !app.isTerminated && Date() < deadline {
                RunLoop.current.run(until: Date().addingTimeInterval(0.05))
            }
            print("\(target.id) pid=\(app.processIdentifier) requested=\(requested) terminated=\(app.isTerminated)")
            guard app.isTerminated else { exit(4) }
        }
    }
} else if operation == "restore" {
    let original = try JSONDecoder().decode([String].self, from: Data(contentsOf: recordURL))
    guard original.allSatisfy({ id in targets.contains { $0.id == id } }) else { exit(5) }
    for target in targets where original.contains(target.id) {
        if matches(target).isEmpty {
            let task = Process()
            task.executableURL = URL(fileURLWithPath: "/usr/bin/open")
            task.arguments = ["-g", target.path]
            try task.run()
            task.waitUntilExit()
            guard task.terminationStatus == 0 else { exit(6) }
        }
        let deadline = Date().addingTimeInterval(5)
        while matches(target).isEmpty && Date() < deadline {
            RunLoop.current.run(until: Date().addingTimeInterval(0.05))
        }
        print("\(target.id) restored=\(!matches(target).isEmpty)")
        guard !matches(target).isEmpty else { exit(7) }
    }
} else {
    exit(2)
}
