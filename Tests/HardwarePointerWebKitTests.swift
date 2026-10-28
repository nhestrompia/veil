import AppKit
import WebKit

@MainActor
final class PointerWebKitCheck: NSObject, WKNavigationDelegate {
    let app: DeviceKeyboardApplication
    let window: AXBoundaryWindow
    let view: AXBoundaryWebView

    init(app: DeviceKeyboardApplication) {
        self.app = app
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        precondition(EngineRuntime.configure(configuration, stable: true))
        precondition(BrowserRuntimePolicy.configureContent(configuration))
        view = AXBoundaryWebView(frame: CGRect(x: 0, y: 0, width: 640, height: 400), configuration: configuration)
        view.isInspectable = false
        window = AXBoundaryWindow(contentRect: view.bounds, styleMask: [.titled, .closable], backing: .buffered, defer: false)
        super.init()
        window.title = "Hardware pointer WebKit dispatch control"
        window.sharingType = .none
        window.contentView = view
        view.navigationDelegate = self
    }

    func start() {
        window.makeKeyAndOrderFront(nil)
        app.activate(ignoringOtherApps: true)
        view.loadHTMLString("""
        <!doctype html><style>button{position:fixed;left:200px;top:150px;width:240px;height:100px}</style>
        <button onclick="window.clicks++; window.last=[event.clientX,event.clientY,event.isTrusted]">Local click control</button>
        <script>window.clicks=0;window.last=[]</script>
        """, baseURL: URL(string: "https://pointer-control.invalid/"))
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        precondition(EngineRuntime.reportContent(view))
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [self] in
            precondition(app.isActive && window.isKeyWindow)
            let poisonedUp = NSEvent.mouseEvent(with: .leftMouseUp, location: CGPoint(x: 2, y: 2),
                modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: window.windowNumber,
                context: nil, eventNumber: 99, clickCount: 1, pressure: 0)!
            app.postEvent(poisonedUp, atStart: true)
            app.dispatchDevicePointerClick(at: view.convert(CGPoint(x: 320, y: 200), to: nil), in: window)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [self] in
                view.evaluateJavaScript("JSON.stringify({clicks:window.clicks,last:window.last})") { [self] value, error in
                    guard error == nil, let text = value as? String,
                          let data = text.data(using: .utf8),
                          let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                          result["clicks"] as? Int == 1,
                          let last = result["last"] as? [Any], last.count == 3,
                          last[0] as? Int == 320, last[1] as? Int == 200 else {
                        print("WEBKIT_POINTER_CONTROL failed=true")
                        fflush(stdout)
                        exit(1)
                    }
                    print("WEBKIT_POINTER_CONTROL \(text)")
                    print("Control scope: internally constructed click, no hardware input, no OS events, no agent attack result.")
                    window.orderOut(nil)
                    fflush(stdout)
                    exit(0)
                }
            }
        }
    }
}

@main
enum HardwarePointerWebKitTests {
    @MainActor static func main() {
        alarm(20)
        let app = DeviceKeyboardApplication.shared as! DeviceKeyboardApplication
        app.setActivationPolicy(.regular)
        app.finishLaunching()
        let check = PointerWebKitCheck(app: app)
        DispatchQueue.main.async { check.start() }
        withExtendedLifetime(check) { app.run() }
    }
}
