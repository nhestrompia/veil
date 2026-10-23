import Foundation

@main enum PolicyTests {
    static func main() {
        let accepted = ["https://example.com", "http://127.0.0.1:8765/fixture", "http://localhost:8765", "http://[::1]:8765"]
        let rejected = ["http://example.com", "javascript:alert(1)", "file:///etc/passwd", "data:text/html,test", "https:relative", "http://localhost.evil.test"]
        for value in accepted { precondition(BrowserPolicy.allows(URL(string: value)!), value) }
        for value in rejected { precondition(!BrowserPolicy.allows(URL(string: value)!), value) }
        precondition(BrowserPolicy.address("example.com")?.absoluteString == "https://example.com")
        precondition(BrowserPolicy.address("") == nil)
        print("Browser policy: 12 cases passed")
    }
}
