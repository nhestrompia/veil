import Foundation

struct PrivateEntryFocus: Sendable {
    let active: Bool
    let key: Bool
    let visible: Bool
    let miniaturized: Bool
    let foreground: Bool

    var eligible: Bool { active && key && visible && !miniaturized && foreground }
}

struct PrivateEntryPolicy {
    private var interval: Range<Double>?

    mutating func begin(now: Double, seconds: Double) -> Bool {
        guard now.isFinite, now >= 0, seconds.isFinite, seconds > 0, seconds <= 10 else {
            interval = nil
            return false
        }
        let deadline = now + seconds
        guard deadline.isFinite, deadline > now else { interval = nil; return false }
        interval = now..<deadline
        return true
    }

    mutating func end() { interval = nil }

    func permits(now: Double, focus: PrivateEntryFocus) -> Bool {
        guard let interval, now.isFinite else { return false }
        return focus.eligible && interval.contains(now)
    }
}
