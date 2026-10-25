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

    static func allowsResponse(url: URL?, canShowMIMEType: Bool, contentDisposition: String?) -> Bool {
        guard let url, allows(url), canShowMIMEType else { return false }
        let disposition = contentDisposition?.split(separator: ";", maxSplits: 1).first?
            .trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return disposition != "attachment"
    }
}
