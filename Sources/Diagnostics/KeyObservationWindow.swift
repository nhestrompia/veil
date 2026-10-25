struct KeyObservationWindow {
    enum Decision: Equatable {
        case wait
        case accept
        case finish(String)
    }

    private enum State {
        case arming(Double)
        case idle(Double)
        case collecting(Double)
        case finished(String)
    }

    private var state: State
    private(set) var collectionStarted = false

    init(now: Double) { state = .arming(now + 5) }

    mutating func observe(now: Double, ownsFocus: Bool, keyArrived: Bool) -> Decision {
        switch state {
        case .finished(let reason): return .finish(reason)
        case .arming(let limit):
            if now >= limit { return finish("Target did not focus within the arming limit") }
            guard ownsFocus else { return .wait }
            state = .idle(now + 60)
        case .idle(let limit):
            if !ownsFocus { return finish("Target lost focus before the sample") }
            if now >= limit { return finish("No key arrived within the idle limit") }
        case .collecting(let limit):
            if !ownsFocus { return finish("Target lost focus during the sample") }
            if now >= limit { return finish("Fifteen-second sample finished") }
            return keyArrived ? .accept : .wait
        }
        guard keyArrived else { return .wait }
        collectionStarted = true
        state = .collecting(now + 15)
        return .accept
    }

    private mutating func finish(_ reason: String) -> Decision {
        state = .finished(reason)
        return .finish(reason)
    }
}
