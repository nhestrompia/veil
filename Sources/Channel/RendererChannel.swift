import Foundation
import Darwin

enum RendererChannelFailure: Error {
    case invalidDescriptor, invalidBootstrap, invalidHeader, oversizedPacket, invalidSession, transport
}

struct RendererPacket: Equatable {
    enum Kind: UInt32 { case navigation = 1, pixels = 2 }
    let kind: Kind
    let sequence: UInt64
    let issuedNanoseconds: UInt64
    let payload: Data
}

struct RendererPacketDecoder {
    static let headerBytes = 48
    static let maximumPixels = 2 * 1024 * 1024
    private let session: Data
    private var buffer = Data()

    init(session: Data) throws {
        guard session.count == 16, session.contains(where: { $0 != 0 }) else { throw RendererChannelFailure.invalidBootstrap }
        self.session = session
    }

    static func encode(_ packet: RendererPacket, session: Data) throws -> Data {
        let maximum = packet.kind == .pixels ? maximumPixels : 2048
        guard packet.payload.count > 0, packet.payload.count <= maximum else { throw RendererChannelFailure.oversizedPacket }
        guard session.count == 16, packet.sequence > 0, packet.issuedNanoseconds > 0 else { throw RendererChannelFailure.invalidHeader }
        var data = Data()
        for value: UInt32 in [0x41464231, packet.kind.rawValue, UInt32(packet.payload.count), 0] {
            var network = value.bigEndian
            withUnsafeBytes(of: &network) { data.append(contentsOf: $0) }
        }
        for value in [packet.sequence, packet.issuedNanoseconds] {
            var network = value.bigEndian
            withUnsafeBytes(of: &network) { data.append(contentsOf: $0) }
        }
        data.append(session)
        data.append(packet.payload)
        return data
    }

    mutating func append(_ data: Data) throws {
        guard buffer.count + data.count <= Self.maximumPixels + Self.headerBytes + 8192 else {
            throw RendererChannelFailure.oversizedPacket
        }
        buffer.append(data)
    }

    mutating func next() throws -> RendererPacket? {
        guard buffer.count >= Self.headerBytes else { return nil }
        func integer(_ offset: Int, _ count: Int) -> UInt64 {
            buffer[(buffer.startIndex + offset)..<(buffer.startIndex + offset + count)]
                .reduce(UInt64(0)) { ($0 << 8) | UInt64($1) }
        }
        guard integer(0, 4) == 0x41464231, integer(12, 4) == 0,
              let kind = RendererPacket.Kind(rawValue: UInt32(integer(4, 4))),
              integer(16, 8) > 0, integer(24, 8) > 0 else { throw RendererChannelFailure.invalidHeader }
        guard buffer[(buffer.startIndex + 32)..<(buffer.startIndex + 48)] == session else {
            throw RendererChannelFailure.invalidSession
        }
        let count = Int(integer(8, 4))
        guard count > 0, count <= (kind == .pixels ? Self.maximumPixels : 2048) else {
            throw RendererChannelFailure.oversizedPacket
        }
        guard buffer.count >= Self.headerBytes + count else { return nil }
        let packet = RendererPacket(kind: kind, sequence: integer(16, 8), issuedNanoseconds: integer(24, 8),
            payload: Data(buffer[(buffer.startIndex + Self.headerBytes)..<(buffer.startIndex + Self.headerBytes + count)]))
        buffer.removeFirst(Self.headerBytes + count)
        return packet
    }

    var bufferedBytes: Int { buffer.count }
}

struct RendererPacketFreshness {
    private(set) var lastSequence: UInt64 = 0

    mutating func accept(_ packet: RendererPacket, now: UInt64, maximumAge: UInt64) -> Bool {
        guard packet.sequence > lastSequence else { return false }
        lastSequence = packet.sequence
        return packet.issuedNanoseconds <= now && now - packet.issuedNanoseconds <= maximumAge
    }
}

@MainActor
final class RendererChannel {
    private let descriptor: Int32
    private let session: Data
    private var decoder: RendererPacketDecoder
    private var outgoing: Data?
    private var offset = 0
    private var latest: Data?
    private var sequence: UInt64 = 0
    private var readSource: (any DispatchSourceRead)?
    private var writeSource: (any DispatchSourceWrite)?
    private(set) var closed = false
    private(set) var wouldBlock = 0
    private(set) var replacedFrames = 0
    private(set) var peakBufferedBytes = 0

    static func now() -> UInt64 {
        var value = timespec()
        precondition(clock_gettime(CLOCK_MONOTONIC, &value) == 0)
        return UInt64(value.tv_sec) * 1_000_000_000 + UInt64(value.tv_nsec)
    }

    init(descriptor: Int32) throws {
        guard descriptor >= 3, descriptor < 1024 else { throw RendererChannelFailure.invalidDescriptor }
        var kind: Int32 = 0
        var size = socklen_t(MemoryLayout<Int32>.size)
        var address = sockaddr_storage()
        var addressSize = socklen_t(MemoryLayout<sockaddr_storage>.size)
        let named = withUnsafeMutablePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { getsockname(descriptor, $0, &addressSize) }
        }
        guard getsockopt(descriptor, SOL_SOCKET, SO_TYPE, &kind, &size) == 0, kind == SOCK_STREAM,
              named == 0, address.ss_family == sa_family_t(AF_UNIX) else { throw RendererChannelFailure.invalidDescriptor }
        let flags = fcntl(descriptor, F_GETFL)
        var enabled: Int32 = 1
        #if CHANNEL_BLOCKING_CONTROL
        let outputFlags = flags & ~O_NONBLOCK
        #else
        let outputFlags = flags | O_NONBLOCK
        #endif
        guard flags >= 0, fcntl(descriptor, F_SETFL, outputFlags) == 0,
              fcntl(descriptor, F_SETFD, FD_CLOEXEC) == 0,
              setsockopt(descriptor, SOL_SOCKET, SO_NOSIGPIPE, &enabled, socklen_t(MemoryLayout<Int32>.size)) == 0 else {
            throw RendererChannelFailure.invalidDescriptor
        }
        var bootstrap = [UInt8](repeating: 0, count: 16)
        let count = bootstrap.withUnsafeMutableBytes { recv(descriptor, $0.baseAddress, $0.count, MSG_DONTWAIT) }
        guard count == 16 else { throw RendererChannelFailure.invalidBootstrap }
        let session = Data(bootstrap)
        decoder = try RendererPacketDecoder(session: session)
        self.session = session
        self.descriptor = descriptor
    }

    func close() {
        guard !closed else { return }
        closed = true
        readSource?.cancel()
        writeSource?.cancel()
        readSource = nil
        writeSource = nil
        Darwin.close(descriptor)
        outgoing = nil
        latest = nil
    }

    func offerPixels(_ data: Data) throws {
        guard !closed else { return }
        let wire = try packet(.pixels, data)
        if outgoing == nil { outgoing = wire }
        else {
            if latest != nil { replacedFrames += 1 }
            latest = wire
        }
        peakBufferedBytes = max(peakBufferedBytes, (outgoing?.count ?? 0) + (latest?.count ?? 0))
        watchWrites()
        flush()
    }

    func navigate(_ url: URL) throws -> Bool {
        guard !closed, outgoing == nil else { return false }
        outgoing = try packet(.navigation, Data(url.absoluteString.utf8))
        peakBufferedBytes = max(peakBufferedBytes, outgoing?.count ?? 0)
        watchWrites()
        flush()
        return true
    }

    private func packet(_ kind: RendererPacket.Kind, _ payload: Data) throws -> Data {
        guard sequence < UInt64.max else { throw RendererChannelFailure.invalidHeader }
        sequence += 1
        return try RendererPacketDecoder.encode(RendererPacket(kind: kind, sequence: sequence,
            issuedNanoseconds: Self.now(), payload: payload), session: session)
    }

    func watchReads(_ handler: @escaping @MainActor () -> Void) {
        guard !closed, readSource == nil else { return }
        let source = DispatchSource.makeReadSource(fileDescriptor: descriptor, queue: .main)
        source.setEventHandler { MainActor.assumeIsolated { handler() } }
        readSource = source
        source.resume()
    }

    private func watchWrites() {
        guard !closed, writeSource == nil else { return }
        let source = DispatchSource.makeWriteSource(fileDescriptor: descriptor, queue: .main)
        source.setEventHandler { [weak self] in MainActor.assumeIsolated { self?.flush() } }
        writeSource = source
        source.resume()
    }

    func flush() {
        guard !closed, let data = outgoing else { return }
        #if CHANNEL_BLOCKING_CONTROL
        let sendFlags: Int32 = 0
        #else
        let sendFlags = MSG_DONTWAIT
        #endif
        let count = data.withUnsafeBytes {
            send(descriptor, $0.baseAddress?.advanced(by: offset), min($0.count - offset, 65536), sendFlags)
        }
        if count > 0 {
            offset += count
            if offset == data.count {
                outgoing = latest
                latest = nil
                offset = 0
                if outgoing == nil {
                    writeSource?.cancel()
                    writeSource = nil
                }
            }
        } else if count < 0, errno == EAGAIN || errno == EWOULDBLOCK { wouldBlock += 1 }
        else if count < 0, errno == EINTR { return }
        else { close() }
    }

    func receive() throws -> [RendererPacket] {
        guard !closed else { return [] }
        var packets: [RendererPacket] = []
        var bytes = 0
        while packets.count < 4 && bytes < 65536 {
            if let packet = try decoder.next() { packets.append(packet); continue }
            var buffer = [UInt8](repeating: 0, count: 8192)
            let count = buffer.withUnsafeMutableBytes { recv(descriptor, $0.baseAddress, $0.count, MSG_DONTWAIT) }
            if count > 0 {
                bytes += count
                try decoder.append(Data(buffer.prefix(count)))
            } else if count == 0 {
                close()
                if decoder.bufferedBytes > 0 { throw RendererChannelFailure.invalidHeader }
                break
            }
            else if errno == EINTR { continue }
            else if errno == EAGAIN || errno == EWOULDBLOCK { break }
            else { close(); throw RendererChannelFailure.transport }
        }
        return packets
    }
}
