import Foundation
import Darwin

enum RendererFilesystemControl {
    static let marker = Array("AFB-filesystem-control\n".utf8)
    static let addition = Array("AFB-test-write\n".utf8)

    static func observe(canary: String) -> [String: Any] {
        ["cwd": FileManager.default.currentDirectoryPath,
         "home": FileManager.default.homeDirectoryForCurrentUser.path,
         "temporary": FileManager.default.temporaryDirectory.path,
         "cache": FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first?.path ?? "",
         "canaryPath": canary, "outside": outsideWrite(path: canary), "temporaryFile": temporaryFile()]
    }

    private static func outsideWrite(path: String) -> [String: Any] {
        let fd = open(path, O_RDWR | O_APPEND | O_NOFOLLOW | O_CLOEXEC)
        guard fd >= 0 else { return ["status": "open-denied", "errno": errno] }
        defer { close(fd) }
        var info = stat()
        var bytes = [UInt8](repeating: 0, count: marker.count)
        guard fstat(fd, &info) == 0, info.st_uid == getuid(),
              info.st_mode & S_IFMT == S_IFREG, info.st_mode & 0o777 == 0o600,
              info.st_size == marker.count, pread(fd, &bytes, bytes.count, 0) == bytes.count,
              bytes == marker else {
            return ["status": "unexpected-canary"]
        }
        let count = addition.withUnsafeBytes { write(fd, $0.baseAddress, $0.count) }
        let writeError = count == addition.count ? 0 : errno
        let synced = count == addition.count && fsync(fd) == 0
        return ["status": count == addition.count && synced ? "appended" : "write-failed",
                "bytes": count, "errno": writeError, "synced": synced]
    }

    private static func temporaryFile() -> [String: Any] {
        let path = FileManager.default.temporaryDirectory
            .appendingPathComponent("afb-filesystem-" + UUID().uuidString).path
        let fd = open(path, O_RDWR | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0o600)
        guard fd >= 0 else { return ["created": false, "errno": errno] }
        let written = marker.withUnsafeBytes { write(fd, $0.baseAddress, $0.count) }
        var bytes = [UInt8](repeating: 0, count: marker.count)
        let read = pread(fd, &bytes, bytes.count, 0)
        close(fd)
        let removed = unlink(path) == 0
        return ["created": true, "written": written == marker.count,
                "readMatched": read == marker.count && bytes == marker, "removed": removed]
    }
}
