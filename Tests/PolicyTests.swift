import Foundation

@main enum PolicyTests {
    static func main() {
        let accepted = ["https://example.com", "http://127.0.0.1:8765/fixture", "http://localhost:8765", "http://[::1]:8765"]
        let rejected = ["http://example.com", "javascript:alert(1)", "file:///etc/passwd", "data:text/html,test", "https:relative", "http://localhost.evil.test"]
        for value in accepted { precondition(BrowserPolicy.allows(URL(string: value)!), value) }
        for value in rejected { precondition(!BrowserPolicy.allows(URL(string: value)!), value) }
        precondition(BrowserPolicy.address("example.com")?.absoluteString == "https://example.com")
        precondition(BrowserPolicy.address("") == nil)
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
