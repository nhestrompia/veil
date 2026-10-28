import AppKit
import WebKit

@MainActor
final class VeilMouseCheck: NSObject, WKNavigationDelegate {
    let app: DeviceKeyboardApplication
    let window: AXBoundaryWindow
    let view: AXBoundaryWebView
    let button = NSButton(title: "Local native control", target: nil, action: nil)
    private var nativeClicks = 0

    init(app: DeviceKeyboardApplication) {
        self.app = app
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        precondition(EngineRuntime.configure(configuration, stable: true))
        precondition(BrowserRuntimePolicy.configureContent(configuration))
        view = AXBoundaryWebView(frame: CGRect(x: 0, y: 0, width: 640, height: 340), configuration: configuration)
        view.isInspectable = false
        window = AXBoundaryWindow(contentRect: CGRect(x: 0, y: 0, width: 640, height: 400),
            styleMask: [.titled, .closable], backing: .buffered, defer: false)
        super.init()
        let content = NSView(frame: CGRect(x: 0, y: 0, width: 640, height: 400))
        content.addSubview(view)
        button.frame = CGRect(x: 200, y: 352, width: 240, height: 32)
        button.target = self
        button.action = #selector(clicked)
        content.addSubview(button)
        window.contentView = content
        window.title = "Veil internal mouse and wheel control"
        window.setFrameOrigin(CGPoint(x: 180, y: 200))
        window.sharingType = .none
        window.acceptsMouseMovedEvents = true
        view.navigationDelegate = self
    }

    @objc private func clicked() { nativeClicks += 1 }

    func start() {
        window.makeKeyAndOrderFront(nil)
        app.activate(ignoringOtherApps: true)
        view.loadHTMLString("""
        <!doctype html><style>body{margin:0;height:5000px}button{position:absolute;left:200px;top:150px;width:240px;height:80px}</style>
        <button onclick="window.clicks++">Local page control</button>
        <script>window.clicks=0;window.moves=0;window.wheels=[];
        addEventListener('pointermove',()=>window.moves++);
        addEventListener('wheel',e=>window.wheels.push([e.deltaY,e.clientX,e.clientY]),{passive:true});</script>
        """, baseURL: URL(string: "https://veil-mouse-control.invalid/"))
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        precondition(EngineRuntime.reportContent(view))
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [self] in
            precondition(app.isActive && window.isKeyWindow)
            let point = view.convert(CGPoint(x: 320, y: 170), to: nil)
            let untrusted = NSEvent.mouseEvent(with: .leftMouseDown, location: point, modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: window.windowNumber,
                context: nil, eventNumber: 99, clickCount: 1, pressure: 1)!
            app.sendEvent(untrusted)
            let untrustedMove = NSEvent.mouseEvent(with: .mouseMoved, location: point, modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: window.windowNumber,
                context: nil, eventNumber: 101, clickCount: 0, pressure: 0)!
            app.sendEvent(untrustedMove)
            let wheel = CGEvent(scrollWheelEvent2Source: nil, units: .line, wheelCount: 1,
                wheel1: -20, wheel2: 0, wheel3: 0)!
            let untrustedWheel = NSEvent(cgEvent: wheel)!
            app.sendEvent(untrustedWheel)
            app.postEvent(untrustedWheel, atStart: true)
            let queued = NSEvent.mouseEvent(with: .leftMouseUp, location: CGPoint(x: 2, y: 2), modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: window.windowNumber,
                context: nil, eventNumber: 100, clickCount: 1, pressure: 0)!
            app.postEvent(queued, atStart: true)
            app.dispatchDevicePointerMove(at: point, in: window)
            app.dispatchDevicePointerClick(at: point, in: window)
            let native = button.convert(CGPoint(x: button.bounds.midX, y: button.bounds.midY), to: nil)
            app.dispatchDevicePointerClick(at: native, in: window)
            app.dispatchDeviceWheel(at: point, lines: -3, in: window)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) { [self] in
                view.evaluateJavaScript("JSON.stringify({clicks:window.clicks,moves:window.moves,wheels:window.wheels,y:scrollY})") { [self] value, error in
                    guard error == nil, let text = value as? String,
                          let data = text.data(using: .utf8),
                          let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { exit(1) }
                    print("VEIL_MOUSE_CONTROL \(text) nativeClicks=\(nativeClicks) refused=\(app.refusedEventCount)")
                    let wheels = result["wheels"] as? [[Double]] ?? []
                    let passed = result["clicks"] as? Int == 1 && nativeClicks == 1
                        && (result["moves"] as? Int ?? 0) > 0
                        && wheels.count == 1 && wheels[0].count == 3
                        && wheels[0][1] == 320 && wheels[0][2] == 170
                        && (result["y"] as? Double ?? 0) > 0 && app.refusedEventCount >= 5
                    print("VEIL_MOUSE_CONTROL passed=\(passed) physicalInputVerified=false externalAttack=false")
                    window.orderOut(nil)
                    fflush(stdout)
                    exit(passed ? 0 : 1)
                }
            }
        }
    }
}

@main
enum VeilMouseWebKitTests {
    @MainActor static func main() {
        alarm(20)
        let app = DeviceKeyboardApplication.shared as! DeviceKeyboardApplication
        app.setActivationPolicy(.regular)
        app.finishLaunching()
        let check = VeilMouseCheck(app: app)
        DispatchQueue.main.async { check.start() }
        withExtendedLifetime(check) { app.run() }
    }
}
