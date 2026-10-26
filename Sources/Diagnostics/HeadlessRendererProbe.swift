import AppKit
import WebKit
import Security
import ObjectiveC.runtime
import Darwin

private struct ProcessRecord: Codable, Equatable {
    let pid: Int32
    let path: String
    let startedSeconds: UInt64
    let startedMicroseconds: UInt64
    let realUID: UInt32
    let effectiveUID: UInt32
    let savedUID: UInt32
    let realGID: UInt32
    let effectiveGID: UInt32
    let savedGID: UInt32

    init?(_ pid: pid_t) {
        guard pid > 1 else { return nil }
        var info = proc_bsdinfo()
        let size = Int32(MemoryLayout<proc_bsdinfo>.size)
        guard proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, size) == size else { return nil }
        var bytes = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
        guard proc_pidpath(pid, &bytes, UInt32(bytes.count)) > 0 else { return nil }
        self.pid = pid
        path = String(decoding: bytes.prefix(while: { $0 != 0 }).map { UInt8(bitPattern: $0) }, as: UTF8.self)
        startedSeconds = info.pbi_start_tvsec
        startedMicroseconds = info.pbi_start_tvusec
        realUID = info.pbi_ruid
        effectiveUID = info.pbi_uid
        savedUID = info.pbi_svuid
        realGID = info.pbi_rgid
        effectiveGID = info.pbi_gid
        savedGID = info.pbi_svgid
    }
}

@MainActor
private final class HeadlessProbe: NSObject, NSApplicationDelegate, WKNavigationDelegate {
    private let output: URL?
    private let nonce = UUID().uuidString
    private let loopbackPort: Int?
    private var view: WKWebView?
    private var finished = false
    private var report: [String: Any] = [:]
    private let filesystemReport: [String: Any]?

    init(output: URL?, loopbackPort: Int?, filesystemReport: [String: Any]? = nil) {
        self.output = output
        self.loopbackPort = loopbackPort
        self.filesystemReport = filesystemReport
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        report["host"] = encoded(ProcessRecord(getpid()))
        report["session"] = sessionRecord()
        report["mode"] = loopbackPort == nil ? "same-user-inline" : "same-user-loopback"
        report["windowCountAtStart"] = NSApp.windows.count
        report["uid"] = getuid()
        report["filesystemControl"] = filesystemReport
        report["resultTransport"] = output == nil ? "bounded-stdout-json" : "workspace-artifact"
        report["explicitSnapshotFileWrites"] = 0
        report["frameworkPath"] = class_getImageName(WKWebView.self).map { String(cString: $0) }
        report["frameworkVersion"] = Bundle(for: WKWebView.self).infoDictionary?["CFBundleVersion"]
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        let webView = WKWebView(frame: NSRect(x: 0, y: 0, width: 800, height: 600), configuration: configuration)
        webView.isInspectable = false
        webView.navigationDelegate = self
        view = webView
        DispatchQueue.main.asyncAfter(deadline: .now() + 20) { [self] in
            finish(error: "probe-deadline")
        }
        if let loopbackPort {
            guard let url = URL(string: "http://127.0.0.1:\(loopbackPort)/fixture/\(nonce)") else {
                finish(error: "invalid-fixed-fixture-url")
                return
            }
            webView.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData))
        } else {
            webView.loadHTMLString("""
        <!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>Headless renderer control</title>
        <style>html,body{margin:0;background:white}div,canvas{position:absolute;top:0;width:100px;height:100px}
        #red{left:0;background:rgb(255,0,0)}#green{left:100px;background:rgb(0,255,0)}canvas{left:200px}</style>
        <div id="red"></div><div id="green"></div><canvas id="blue" width="100" height="100"></canvas>
        <script>window.testNonce='\(nonce)';let c=document.getElementById('blue').getContext('2d');
        c.fillStyle='rgb(0,0,255)';c.fillRect(0,0,100,100);</script>
        """, baseURL: nil)
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction) async -> WKNavigationActionPolicy {
        guard let url = navigationAction.request.url else { return .cancel }
        if loopbackPort == nil { return url.absoluteString == "about:blank" ? .allow : .cancel }
        let route = navigationAction.targetFrame?.isMainFrame == true ? "fixture" : "frame"
        return url.scheme == "http" && url.host == "127.0.0.1" && url.port == loopbackPort
            && url.path == "/\(route)/\(nonce)" && url.query == nil && url.fragment == nil
            && url.user == nil && url.password == nil ? .allow : .cancel
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        Task { @MainActor in
            do {
                let value = try await webView.callAsyncJavaScript("""
                await window.fixtureReady;
                return {nonce:window.testNonce,width:innerWidth,height:innerHeight,
                  canvas:Array.from(document.getElementById('blue').getContext('2d').getImageData(20,20,1,1).data),
                  fetchedNonce:window.fetchedNonce ?? null,
                  frameNonce:document.getElementById('child')?.contentWindow.frameNonce ?? null,
                  imageWidth:document.getElementById('remote')?.naturalWidth ?? null};
                """, arguments: [:], in: nil, contentWorld: .page)
                guard !finished else { return }
                let js = value as? [String: Any] ?? [:]
                report["javascript"] = js
                report["javascriptPassed"] = js["nonce"] as? String == nonce
                    && (js["width"] as? Int) == 800 && (js["height"] as? Int) == 600
                    && (js["canvas"] as? [Int]) == [0, 0, 255, 255]
                if loopbackPort != nil {
                    report["networkDocumentPassed"] = js["fetchedNonce"] as? String == nonce
                        && js["frameNonce"] as? String == nonce && js["imageWidth"] as? Int == 1
                }
                let before = identities(webView)
                report["servicesBeforeSnapshot"] = before
                let config = WKSnapshotConfiguration()
                config.rect = NSRect(x: 0, y: 0, width: 800, height: 600)
                config.snapshotWidth = 800
                let image = try await webView.takeSnapshot(configuration: config)
                guard !finished else { return }
                try recordSnapshot(image)
                let after = identities(webView)
                report["servicesAfterSnapshot"] = after
                report["serviceIdentityStable"] = NSDictionary(dictionary: before).isEqual(to: after)
                finish()
            } catch {
                finish(error: String(describing: error))
            }
        }
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        finish(error: String(describing: error))
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        finish(error: "web-content-process-terminated")
    }

    private func recordSnapshot(_ image: NSImage) throws {
        guard let tiff = image.tiffRepresentation,
              let original = NSBitmapImageRep(data: tiff),
              let png = original.representation(using: .png, properties: [:]),
              let bitmap = NSBitmapImageRep(data: png) else {
            throw NSError(domain: "HeadlessRendererProbe", code: 1)
        }
        guard png.count <= 2 * 1024 * 1024 else {
            throw NSError(domain: "HeadlessRendererProbe", code: 2)
        }
        if let output {
            try png.write(to: output.appendingPathComponent("snapshot.png"), options: .withoutOverwriting)
            report["explicitSnapshotFileWrites"] = 1
        } else {
            report["snapshotPNGBase64"] = png.base64EncodedString()
        }
        var expected = [(50, 50, [255, 0, 0]), (150, 50, [0, 255, 0]),
                        (250, 50, [0, 0, 255]), (400, 200, [255, 255, 255])]
        if loopbackPort != nil { expected += [(350, 50, [255, 255, 0]), (50, 250, [0, 255, 255])] }
        var samples: [[String: Any]] = []
        var passed = bitmap.pixelsWide >= 800 && bitmap.pixelsHigh >= 600
            && bitmap.pixelsWide * 600 == bitmap.pixelsHigh * 800
            && bitmap.bitsPerSample == 8 && bitmap.samplesPerPixel == 4
            && !bitmap.bitmapFormat.contains(.alphaFirst)
        for (x, y, rgb) in expected {
            let px = x * bitmap.pixelsWide / 800
            let py = y * bitmap.pixelsHigh / 600
            var components = [Int](repeating: 0, count: bitmap.samplesPerPixel)
            bitmap.getPixel(&components, atX: px, y: py)
            let observed = Array(components.prefix(3))
            let matches = components.count == 4 && components[3] == 255
                && zip(observed, rgb).allSatisfy { abs($0 - $1) <= 5 }
            samples.append(["point": [x, y], "expected": rgb, "observed": observed, "passed": matches])
            passed = passed && matches
        }
        report["snapshot"] = ["width": bitmap.pixelsWide, "height": bitmap.pixelsHigh, "samples": samples,
                              "bitsPerSample": bitmap.bitsPerSample, "samplesPerPixel": bitmap.samplesPerPixel,
                              "colorSpace": bitmap.colorSpaceName.rawValue]
        report["snapshotPassed"] = passed
    }

    private func identities(_ webView: WKWebView) -> [String: Any] {
        let receivers: [(String, NSObject, String)] = [
            ("content", webView, "_webProcessIdentifier"),
            ("gpu", webView, "_gpuProcessIdentifier"),
            ("network", webView.configuration.websiteDataStore, "_networkProcessIdentifier")
        ]
        var records: [String: Any] = [:]
        for (name, receiver, methodName) in receivers {
            let selector = NSSelectorFromString(methodName)
            guard let method = class_getInstanceMethod(type(of: receiver), selector),
                  method_getNumberOfArguments(method) == 2 else {
                records[name] = ["status": "getter-unavailable"]
                continue
            }
            let returnType = method_copyReturnType(method)
            defer { free(returnType) }
            guard String(cString: returnType) == "i" else {
                records[name] = ["status": "unexpected-getter-signature"]
                continue
            }
            typealias Getter = @convention(c) (AnyObject, Selector) -> Int32
            let getter = unsafeBitCast(method_getImplementation(method), to: Getter.self)
            let pid = getter(receiver, selector)
            records[name] = ["pid": pid, "identity": encoded(ProcessRecord(pid)),
                             "networkGetterCanLaunchService": name == "network"]
        }
        return records
    }

    private func sessionRecord() -> [String: Any] {
        var session: SecuritySessionId = 0
        var attributes = SessionAttributeBits(rawValue: 0)
        let status = SessionGetInfo(callerSecuritySession, &session, &attributes)
        var record: [String: Any] = ["status": status, "sessionID": session, "attributes": attributes.rawValue]
        let dictionary = CGSessionCopyCurrentDictionary() as? [String: Any]
        record["consoleDictionaryAvailable"] = dictionary != nil
        for (name, key) in [("userID", kCGSessionUserIDKey), ("onConsole", kCGSessionOnConsoleKey),
                            ("loginDone", kCGSessionLoginDoneKey)] {
            record[name] = dictionary?[key as String]
        }
        return record
    }

    private func encoded<T: Encodable>(_ value: T?) -> Any {
        guard let value, let data = try? JSONEncoder().encode(value),
              let object = try? JSONSerialization.jsonObject(with: data) else { return NSNull() }
        return object
    }

    private func finish(error: String? = nil) {
        guard !finished else { return }
        finished = true
        report["error"] = error
        #if RENDERER_FILESYSTEM_CONTROL
        if let view {
            report["servicesAtFinish"] = identities(view)
            report["finishIdentityNetworkGetterCanLaunchService"] = true
        }
        #endif
        report["windowCountAtEnd"] = NSApp.windows.count
        report["windowsAtEnd"] = NSApp.windows.map {
            ["class": NSStringFromClass(type(of: $0)), "visible": $0.isVisible, "key": $0.isKeyWindow] as [String: Any]
        }
        report["visibleWindowCountAtEnd"] = NSApp.windows.filter(\.isVisible).count
        report["completed"] = error == nil
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]),
           let line = String(data: data, encoding: .utf8) {
            print("HEADLESS_RENDERER_RESULT " + line)
            fflush(stdout)
        }
        view?.stopLoading()
        #if RENDERER_FILESYSTEM_CONTROL
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [self] in
            view = nil
            NSApp.terminate(nil)
        }
        #else
        view = nil
        NSApp.terminate(nil)
        #endif
    }
}

@main
private enum HeadlessRendererMain {
    @MainActor static func main() {
        let args = CommandLine.arguments
        guard getuid() != 0, geteuid() != 0, args.count == 2 || args.count == 4 else { exit(64) }
        #if RENDERER_FILESYSTEM_CONTROL
        guard args.count == 4, args[1] == "--pipe-only", args[2] == "--canary" else { exit(64) }
        let canary = URL(fileURLWithPath: args[3]).standardizedFileURL
        let artifactRoot = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().appendingPathComponent("artifacts").path
        guard canary.path == args[3], canary.path.hasPrefix(artifactRoot + "/"),
              canary.lastPathComponent == "outside-canary" else { exit(64) }
        let filesystemReport: [String: Any]? = RendererFilesystemControl.observe(canary: canary.path)
        let port: Int? = nil
        let output: URL? = nil
        #else
        let pipeOnly = args.count == 2 && args[1] == "--pipe-only"
        let filesystemReport: [String: Any]? = nil
        var port: Int?
        if args.count == 4 {
            guard args[2] == "--loopback-port", let value = Int(args[3]), (1024...65535).contains(value) else { exit(64) }
            port = value
        }
        var output: URL?
        if !pipeOnly {
            let directory = URL(fileURLWithPath: args[1]).standardizedFileURL
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
                .deletingLastPathComponent().appendingPathComponent("artifacts").resolvingSymlinksInPath()
            guard directory.resolvingSymlinksInPath().path == directory.path,
                  directory.path.hasPrefix(root.path + "/"),
                  (try? FileManager.default.contentsOfDirectory(atPath: directory.path))?.isEmpty == true else { exit(64) }
            output = directory
        }
        #endif
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let delegate = HeadlessProbe(output: output, loopbackPort: port, filesystemReport: filesystemReport)
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}
