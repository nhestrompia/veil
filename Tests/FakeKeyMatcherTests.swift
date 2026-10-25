@main
struct FakeKeyMatcherTests {
    static func main() {
        let phrase: [Int64] = [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17]
        var full = FakeKeyMatcher()
        for code in phrase { full.consume(code) }
        precondition(full.matched)

        var partial = FakeKeyMatcher()
        for code in phrase.dropLast() { partial.consume(code) }
        precondition(!partial.matched)

        var overlapping = FakeKeyMatcher()
        for code in phrase.prefix(8) + phrase { overlapping.consume(code) }
        precondition(overlapping.matched)

        var interrupted = FakeKeyMatcher()
        for code in phrase.prefix(5) + [999] + phrase.suffix(7) { interrupted.consume(code) }
        precondition(!interrupted.matched)

        var repeated = FakeKeyMatcher()
        for code in [999, 45, 45] + phrase + phrase { repeated.consume(code) }
        precondition(repeated.matched)
        print("Five fixed fake-key sequence checks passed.")
    }
}
