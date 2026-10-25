import Foundation

struct BrowserPolicy {
    static func allows(_ url: URL) -> Bool {
        if url.scheme == "https" { return url.host != nil }
        return url.scheme == "http" && ["127.0.0.1", "localhost", "::1", "[::1]"].contains(url.host)
    }

    static func address(_ text: String) -> URL? {
        let value = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty,
              let url = URL(string: value.contains("://") ? value : "https://" + value),
              allows(url) else { return nil }
        return url
    }

    static func allowsNavigation(_ url: URL, isMainFrame: Bool) -> Bool {
        if allows(url) { return true }
        guard !isMainFrame, let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return false }
        return components.scheme == "about" && components.host == nil && components.query == nil &&
            ["blank", "srcdoc"].contains(components.percentEncodedPath)
    }

    static func allowsResponse(url: URL?, canShowMIMEType: Bool, contentDisposition: String?, isMainFrame: Bool = true) -> Bool {
        guard let url, allowsNavigation(url, isMainFrame: isMainFrame), canShowMIMEType else { return false }
        let disposition = contentDisposition?.split(separator: ";", maxSplits: 1).first?
            .trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return disposition != "attachment"
    }
}
