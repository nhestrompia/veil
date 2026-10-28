import Foundation
import Darwin

@main
private enum RendererChannelTests {
    @MainActor static func main() throws {
        var checks = 0
        func check(_ condition: Bool) { precondition(condition); checks += 1 }
        func refuses(_ body: () throws -> Void) {
            do { try body(); preconditionFailure("Expected refusal") } catch { checks += 1 }
        }
        let token = Data(1...16)
        let packet = RendererPacket(kind: .navigation, sequence: 1, issuedNanoseconds: 100,
                                    payload: Data("https://example.invalid/".utf8))
        let wire = try RendererPacketDecoder.encode(packet, session: token)
        check(wire.count == 48 + packet.payload.count)
        for split in 0..<wire.count {
            var decoder = try RendererPacketDecoder(session: token)
            try decoder.append(Data(wire.prefix(split)))
            check(try decoder.next() == nil)
            try decoder.append(Data(wire.dropFirst(split)))
            check(try decoder.next() == packet)
            check(try decoder.next() == nil)
        }
        var decoder = try RendererPacketDecoder(session: token)
        for byte in wire { try decoder.append(Data([byte])) }
        check(try decoder.next() == packet)
        try decoder.append(wire + wire)
        check(try decoder.next() == packet)
        check(try decoder.next() == packet)
        check(try decoder.next() == nil)
        for (index, value): (Int, UInt8) in [(0, 0), (7, 3), (15, 1), (23, 0), (31, 0), (32, 0)] {
            var damaged = wire
            damaged[index] = value
            if index == 23 || index == 31 {
                damaged.replaceSubrange(index-3...index, with: [0, 0, 0, 0])
            }
            refuses {
                var decoder = try RendererPacketDecoder(session: token)
                try decoder.append(damaged)
                _ = try decoder.next()
            }
        }
        refuses { _ = try RendererPacketDecoder(session: Data(repeating: 0, count: 16)) }
        refuses {
            _ = try RendererPacketDecoder.encode(RendererPacket(kind: .navigation, sequence: 1,
                issuedNanoseconds: 1, payload: Data(repeating: 1, count: 2049)), session: token)
        }
        refuses {
            var decoder = try RendererPacketDecoder(session: token)
            try decoder.append(Data(repeating: 1, count: 2 * 1024 * 1024 + 48 + 8193))
        }
        for length: UInt32 in [0, 2049, UInt32.max] {
            var damaged = wire
            var network = length.bigEndian
            withUnsafeBytes(of: &network) { damaged.replaceSubrange(8..<12, with: $0) }
            refuses {
                var decoder = try RendererPacketDecoder(session: token)
                try decoder.append(damaged)
                _ = try decoder.next()
            }
        }
        var freshness = RendererPacketFreshness()
        check(freshness.accept(packet, now: 110, maximumAge: 20))
        check(!freshness.accept(packet, now: 110, maximumAge: 20))
        let stale = RendererPacket(kind: .navigation, sequence: 2, issuedNanoseconds: 100, payload: packet.payload)
        check(!freshness.accept(stale, now: 121, maximumAge: 20))
        let replay = RendererPacket(kind: .navigation, sequence: 2, issuedNanoseconds: 122, payload: packet.payload)
        check(!freshness.accept(replay, now: 122, maximumAge: 20))
        let future = RendererPacket(kind: .navigation, sequence: 3, issuedNanoseconds: 200, payload: packet.payload)
        check(!freshness.accept(future, now: 199, maximumAge: 20))
        var sockets: [Int32] = [-1, -1]
        check(socketpair(AF_UNIX, SOCK_STREAM, 0, &sockets) == 0)
        for fd in sockets {
            var capacity: Int32 = 1024
            check(setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &capacity, socklen_t(MemoryLayout<Int32>.size)) == 0)
            check(token.withUnsafeBytes { send(fd, $0.baseAddress, $0.count, 0) } == 16)
        }
        let writer = try RendererChannel(descriptor: sockets[0])
        let reader = try RendererChannel(descriptor: sockets[1])
        defer { writer.close(); reader.close() }
        check(fcntl(sockets[0], F_GETFD) & FD_CLOEXEC != 0)
        for _ in 0..<30 { try writer.offerPixels(Data(repeating: 42, count: 100_000)) }
        check(writer.wouldBlock > 0)
        check(writer.replacedFrames > 0)
        check(writer.peakBufferedBytes <= 200_096)
        var received: [RendererPacket] = []
        for _ in 0..<1000 {
            writer.flush()
            received += try reader.receive()
            if received.count == 2 { break }
        }
        check(received.map(\.sequence) == [1, 30])
        check(received.allSatisfy { $0.payload == Data(repeating: 42, count: 100_000) })
        reader.close()
        try writer.offerPixels(Data([1]))
        writer.flush()
        check(writer.closed)
        refuses { _ = try RendererChannel(descriptor: 0) }
        var truncatedSockets: [Int32] = [-1, -1]
        check(socketpair(AF_UNIX, SOCK_STREAM, 0, &truncatedSockets) == 0)
        check(token.withUnsafeBytes { send(truncatedSockets[0], $0.baseAddress, $0.count, 0) } == 16)
        let truncatedReader = try RendererChannel(descriptor: truncatedSockets[1])
        defer { truncatedReader.close(); Darwin.close(truncatedSockets[0]) }
        check(wire.withUnsafeBytes { send(truncatedSockets[0], $0.baseAddress, 20, 0) } == 20)
        check(shutdown(truncatedSockets[0], SHUT_WR) == 0)
        refuses { _ = try truncatedReader.receive() }
        check(truncatedReader.closed)
        let report: [String: Any] = ["passed": true, "checks": checks, "rootRun": false,
            "fragmentSplits": wire.count, "nonblockingBackpressure": true, "latestFrameRetained": true,
            "closedPeerWithoutSIGPIPE": true]
        print(String(decoding: try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]), as: UTF8.self))
    }
}
