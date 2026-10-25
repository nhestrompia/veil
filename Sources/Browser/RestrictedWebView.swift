import AppKit
import WebKit

@MainActor
class RestrictedWebView: WKWebView {
    override func menu(for event: NSEvent) -> NSMenu? { nil }
    override func rightMouseDown(with event: NSEvent) {}
    override func validRequestor(forSendType sendType: NSPasteboard.PasteboardType?,
                                returnType: NSPasteboard.PasteboardType?) -> Any? { nil }

    @objc(copy:) func refuseCopy(_ sender: Any?) { refuseExport("copy") }
    @objc(cut:) func refuseCut(_ sender: Any?) { refuseExport("cut") }
    @objc(paste:) func refusePaste(_ sender: Any?) { refuseExport("paste") }
    @objc(pasteAsPlainText:) func refusePlainPaste(_ sender: Any?) { refuseExport("paste") }
    @objc(pasteAsRichText:) func refuseRichPaste(_ sender: Any?) { refuseExport("paste") }
    override func printView(_ sender: Any?) { refuseExport("print") }

    @objc(writeSelectionToPasteboard:types:)
    func refuseSelectionWrite(_ pasteboard: NSPasteboard, types: [NSPasteboard.PasteboardType]) -> Bool {
        refuseExport("selection-write")
        return false
    }

    @objc(readSelectionFromPasteboard:)
    func refuseSelectionRead(_ pasteboard: NSPasteboard) -> Bool {
        refuseExport("selection-read")
        return false
    }

    @objc(readSelectionFromPasteboard:type:)
    func refuseTypedSelectionRead(_ pasteboard: NSPasteboard, type: NSPasteboard.PasteboardType) -> Bool {
        refuseExport("selection-read")
        return false
    }

    private func refuseExport(_ kind: String) {
        print("CONTENT_EXPORT_REFUSED kind=\(kind)")
        fflush(stdout)
    }
}
