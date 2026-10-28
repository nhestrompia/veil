import AppKit
import Foundation
import Security

guard CommandLine.arguments.count == 2, let pid = Int32(CommandLine.arguments[1]),
      let app = NSRunningApplication(processIdentifier: pid),
      app.bundleIdentifier == "research.agentfreebrowser.devicekeyboard", let bundleURL = app.bundleURL else {
    exit(2)
}
var guest: SecCode?
let guestStatus = SecCodeCopyGuestWithAttributes(nil, [kSecGuestAttributePid: NSNumber(value: pid)] as CFDictionary, [], &guest)
func details(_ code: SecStaticCode) -> [String: Any] {
    var raw: CFDictionary?
    let status = SecCodeCopySigningInformation(code, SecCSFlags(rawValue: kSecCSSigningInformation), &raw)
    let info = raw as? [String: Any] ?? [:]
    let hash = (info[kSecCodeInfoUnique as String] as? Data)?.map { String(format: "%02x", $0) }.joined()
    return ["status": status, "cdhash": hash as Any? ?? NSNull(),
            "identifier": info[kSecCodeInfoIdentifier as String] as? String ?? "unavailable"]
}
var result: [String: Any] = ["guestStatus": guestStatus, "pid": pid,
    "scope": "Read-only research-app code validity. Signing-information hashes describe static code, not a kernel hash."]
if let guest {
    var associated: SecStaticCode?
    result["guestStaticStatus"] = SecCodeCopyStaticCode(guest, [], &associated)
    if let associated { result["guestStaticIdentity"] = details(associated) }
    result["dynamicValidity"] = SecCodeCheckValidity(guest, [], nil)
}
var staticCode: SecStaticCode?
let staticStatus = SecStaticCodeCreateWithPath(bundleURL as CFURL, [], &staticCode)
result["staticStatus"] = staticStatus
if let staticCode {
    var raw: CFDictionary?
    let status = SecCodeCopySigningInformation(staticCode, SecCSFlags(rawValue: kSecCSSigningInformation), &raw)
    let info = raw as? [String: Any] ?? [:]
    let hash = (info[kSecCodeInfoUnique as String] as? Data)?.map { String(format: "%02x", $0) }.joined()
    result["static"] = ["status": status, "cdhash": hash as Any? ?? NSNull()]
}
let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
print(String(decoding: data, as: UTF8.self))
