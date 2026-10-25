@main
struct KeyObservationWindowTests {
    static func main() {
        var waiting = KeyObservationWindow(now: 0)
        precondition(waiting.observe(now: 1, ownsFocus: false, keyArrived: true) == .wait)
        precondition(!waiting.collectionStarted)
        precondition(waiting.observe(now: 2, ownsFocus: true, keyArrived: false) == .wait)
        precondition(waiting.observe(now: 25, ownsFocus: true, keyArrived: true) == .accept)
        precondition(waiting.collectionStarted)
        precondition(waiting.observe(now: 39, ownsFocus: true, keyArrived: true) == .accept)
        if case .finish = waiting.observe(now: 40, ownsFocus: true, keyArrived: true) {} else { preconditionFailure() }

        var expired = KeyObservationWindow(now: 0)
        if case .finish = expired.observe(now: 5, ownsFocus: false, keyArrived: true) {} else { preconditionFailure() }
        precondition(!expired.collectionStarted)

        var idle = KeyObservationWindow(now: 0)
        precondition(idle.observe(now: 1, ownsFocus: true, keyArrived: false) == .wait)
        if case .finish = idle.observe(now: 61, ownsFocus: true, keyArrived: true) {} else { preconditionFailure() }

        var focus = KeyObservationWindow(now: 0)
        precondition(focus.observe(now: 1, ownsFocus: true, keyArrived: true) == .accept)
        if case .finish = focus.observe(now: 2, ownsFocus: false, keyArrived: true) {} else { preconditionFailure() }
        if case .finish = focus.observe(now: 3, ownsFocus: true, keyArrived: true) {} else { preconditionFailure() }
        print("Observation readiness, idle, focus, and collection limits passed.")
    }
}
