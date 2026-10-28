struct FakeKeyMatcher {
    private static let expected: [Int64] = [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17]
    private static let fallback = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
    private var prefixLength = 0
    private(set) var matched = false

    mutating func consume(_ code: Int64) {
        while prefixLength > 0, code != Self.expected[prefixLength] {
            prefixLength = Self.fallback[prefixLength - 1]
        }
        if code == Self.expected[prefixLength] { prefixLength += 1 }
        if prefixLength == Self.expected.count {
            matched = true
            prefixLength = Self.fallback[prefixLength - 1]
        }
    }
}
