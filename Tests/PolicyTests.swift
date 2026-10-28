import Foundation

@main enum PolicyTests {
    static func main() {
        let accepted = ["https://example.com", "http://127.0.0.1:8765/fixture", "http://localhost:8765", "http://[::1]:8765"]
        let rejected = ["http://example.com", "javascript:alert(1)", "file:///etc/passwd", "data:text/html,test", "https:relative", "http://localhost.evil.test"]
        for value in accepted { precondition(BrowserPolicy.allows(URL(string: value)!), value) }
        for value in rejected { precondition(!BrowserPolicy.allows(URL(string: value)!), value) }
        precondition(BrowserPolicy.address("example.com")?.absoluteString == "https://example.com")
        precondition(BrowserPolicy.address("") == nil)
        for value in ["about:blank", "about:srcdoc", "about:blank#section"] {
            let embedded = URL(string: value)!
            precondition(BrowserPolicy.allowsNavigation(embedded, isMainFrame: false), value)
            precondition(!BrowserPolicy.allowsNavigation(embedded, isMainFrame: true), value)
            precondition(!BrowserPolicy.allows(embedded), value)
            precondition(BrowserPolicy.allowsResponse(url: embedded, canShowMIMEType: true, contentDisposition: nil, isMainFrame: false), value)
            precondition(!BrowserPolicy.allowsResponse(url: embedded, canShowMIMEType: true, contentDisposition: nil), value)
        }
        for value in ["about:config", "about:srcdoc?source=remote", "about://blank", "about:%73rcdoc", "data:text/html,test", "javascript:alert(1)", "file:///tmp/page.html"] {
            precondition(!BrowserPolicy.allowsNavigation(URL(string: value)!, isMainFrame: false), value)
        }
        let page = URL(string: "https://example.com/page")!
        precondition(BrowserPolicy.allowsResponse(url: page, canShowMIMEType: true, contentDisposition: nil))
        precondition(BrowserPolicy.allowsResponse(url: page, canShowMIMEType: true, contentDisposition: "inline; filename=a.html"))
        for disposition in ["attachment", " ATTACHMENT ; filename=a.html"] {
            precondition(!BrowserPolicy.allowsResponse(url: page, canShowMIMEType: true, contentDisposition: disposition))
        }
        precondition(!BrowserPolicy.allowsResponse(url: page, canShowMIMEType: false, contentDisposition: nil))
        precondition(!BrowserPolicy.allowsResponse(url: URL(string: "file:///tmp/page.html"), canShowMIMEType: true, contentDisposition: nil))
        precondition(!BrowserPolicy.allowsResponse(url: nil, canShowMIMEType: true, contentDisposition: nil))
        print("Browser address and response policy checks passed")
    }
}
