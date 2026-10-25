import AppKit

let args = CommandLine.arguments
if args.count == 2, let pid = Int32(args[1]) {
    guard let target = NSRunningApplication(processIdentifier: pid),
          ["research.agentfreebrowser.control", "research.agentfreebrowser.devicekeyboard"].contains(target.bundleIdentifier ?? "") else { exit(2) }
    _ = target.activate(options: [])
    RunLoop.current.run(until: Date().addingTimeInterval(0.3))
} else if args.count != 1 {
    exit(2)
}
print(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1)
