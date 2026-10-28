@main
enum PrivateEntryPolicyTests {
    static func main() {
        var checks = 0
        func check(_ value: Bool) { precondition(value); checks += 1 }
        var policy = PrivateEntryPolicy()
        let focused = PrivateEntryFocus(active: true, key: true, visible: true, miniaturized: false, foreground: true)
        check(!policy.permits(now: 1, focus: focused))
        check(policy.begin(now: 1, seconds: 10))
        for bits in 0..<32 {
            let focus = PrivateEntryFocus(active: bits & 1 != 0, key: bits & 2 != 0, visible: bits & 4 != 0,
                                          miniaturized: bits & 8 != 0, foreground: bits & 16 != 0)
            check(policy.permits(now: 2, focus: focus) == (bits == 23))
        }
        check(policy.permits(now: 10.999, focus: focused))
        for now in [0.0, 11, 12, -1, Double.nan, Double.infinity] { check(!policy.permits(now: now, focus: focused)) }
        policy.end()
        check(!policy.permits(now: 2, focus: focused))
        for duration in [-1.0, 0, 11, Double.nan, Double.infinity] {
            check(!policy.begin(now: 1, seconds: duration))
            check(!policy.permits(now: 2, focus: focused))
        }
        for now in [-1.0, Double.nan, Double.infinity, Double.greatestFiniteMagnitude] { check(!policy.begin(now: now, seconds: 10)) }
        print("Private entry policy passed \(checks) pure checks. No native input protection was enabled.")
    }
}
