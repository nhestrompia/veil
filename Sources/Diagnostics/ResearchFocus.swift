import AppKit

let args = CommandLine.arguments
if (args.count == 2 || (args.count == 3 && ["--hide", "--unhide"].contains(args[1]))), let pid = Int32(args.last ?? "") {
    guard let target = NSRunningApplication(processIdentifier: pid),
          ["research.agentfreebrowser.control", "research.agentfreebrowser.devicekeyboard",
           "research.agentfreebrowser.internalkeyboardcontrol"].contains(target.bundleIdentifier ?? "") else { exit(2) }
    if args.count == 3 {
        let succeeded = args[1] == "--hide" ? target.hide() : target.unhide()
        print("operationSucceeded=\(succeeded)")
    } else {
        _ = target.activate(options: [])
    }
    RunLoop.current.run(until: Date().addingTimeInterval(0.3))
    if args.count == 3 { print("targetHidden=\(target.isHidden)") }
} else if args.count != 1 {
    exit(2)
}
print(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1)
