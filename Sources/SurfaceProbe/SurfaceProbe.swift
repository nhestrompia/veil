import Foundation
import IOSurface
import CoreVideo

enum SurfaceKind: String { case direct, pixelBuffer }
enum SurfacePolicy: String { case defaults, local, global }

struct SurfaceFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

func output(_ value: [String: Any]) throws {
    let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
    print(String(decoding: data, as: UTF8.self))
    fflush(stdout)
}

@main
enum SurfaceProbe {
    static func main() {
        do { try run(Array(CommandLine.arguments.dropFirst())) }
        catch { try? output(["status": "inconclusive", "error": String(describing: error)]); exit(2) }
    }

    static func run(_ args: [String]) throws {
        if args.first == "read", args.count == 2, let id = UInt32(args[1]) {
            guard let surface = IOSurfaceLookup(id) else {
                try output(["status": "lookup-unavailable", "surfaceID": id])
                return
            }
            let lock = IOSurfaceLock(surface, .readOnly, nil)
            guard lock == kIOReturnSuccess else { throw SurfaceFailure("Surface lock failed: \(lock)") }
            defer { IOSurfaceUnlock(surface, .readOnly, nil) }
            guard IOSurfaceGetAllocSize(surface) >= MemoryLayout<UInt64>.size else { throw SurfaceFailure("No readable fake surface bytes") }
            let address = IOSurfaceGetBaseAddress(surface)
            let nonce = address.load(as: UInt64.self)
            try output(["status": "read", "surfaceID": id, "observedNonce": String(nonce, radix: 16)])
            return
        }
        guard args.first == "write", args.count == 3, let kind = SurfaceKind(rawValue: args[1]),
              let policy = SurfacePolicy(rawValue: args[2]) else {
            throw SurfaceFailure("Use write direct|pixelBuffer defaults|local|global, or read ID")
        }
        var options: [String: Any] = [:]
        // This deprecated key is the explicit subject of the isolated global-lookup control.
        if policy != .defaults { options[kIOSurfaceIsGlobal as String] = policy == .global }
        var buffer: CVPixelBuffer?
        let surface: IOSurfaceRef
        switch kind {
        case .direct:
            options[kIOSurfaceWidth as String] = 16
            options[kIOSurfaceHeight as String] = 16
            options[kIOSurfaceBytesPerElement as String] = 4
            options[kIOSurfaceBytesPerRow as String] = 64
            options[kIOSurfaceAllocSize as String] = 1024
            options[kIOSurfacePixelFormat as String] = kCVPixelFormatType_32BGRA
            guard let created = IOSurfaceCreate(options as CFDictionary) else { throw SurfaceFailure("Direct allocation failed") }
            surface = created
        case .pixelBuffer:
            let attributes = [kCVPixelBufferIOSurfacePropertiesKey: options] as CFDictionary
            let result = CVPixelBufferCreate(kCFAllocatorDefault, 16, 16, kCVPixelFormatType_32BGRA, attributes, &buffer)
            guard result == kCVReturnSuccess, let buffer,
                  let created = CVPixelBufferGetIOSurface(buffer)?.takeUnretainedValue() else {
                throw SurfaceFailure("Pixel buffer has no IOSurface backing")
            }
            surface = created
        }
        let nonce = UInt64.random(in: 1...UInt64.max)
        let lock = IOSurfaceLock(surface, [], nil)
        guard lock == kIOReturnSuccess else { throw SurfaceFailure("Writer lock failed: \(lock)") }
        guard IOSurfaceGetAllocSize(surface) >= MemoryLayout<UInt64>.size else {
            IOSurfaceUnlock(surface, [], nil)
            throw SurfaceFailure("Writer has no fake surface bytes")
        }
        let address = IOSurfaceGetBaseAddress(surface)
        address.storeBytes(of: nonce, as: UInt64.self)
        IOSurfaceUnlock(surface, [], nil)
        try output(["status": "ready", "surfaceID": IOSurfaceGetID(surface), "expectedNonce": String(nonce, radix: 16),
                    "kind": kind.rawValue, "policy": policy.rawValue])
        // Only the controller receives the expected value. The reader receives this exact fake ID.
        withExtendedLifetime((surface, buffer)) { _ = readLine() }
    }
}
